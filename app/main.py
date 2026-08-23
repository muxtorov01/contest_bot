"""Bot uchun kirish nuqtasi. Railway'da webhook orqali ishlaydi."""
from __future__ import annotations

import asyncio
import subprocess
import sys

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application
from aiohttp import web

from app.config import settings
from app.middlewares.db_session import DbSessionMiddleware
from app.middlewares.role import RoleMiddleware
from app.middlewares.throttling import ThrottlingMiddleware
from app.scheduler.jobs import setup_scheduler
from app.utils.logger import logger

# --- Handlerlar ---
from app.handlers.user import start as user_start
from app.handlers.user import captcha as user_captcha
from app.handlers.user import menu as user_menu
from app.handlers.admin import panel as admin_panel
from app.handlers.admin import search as admin_search
from app.handlers.admin import export as admin_export
from app.handlers.superadmin import contest as sa_contest
from app.handlers.superadmin import channels as sa_channels
from app.handlers.superadmin import admins as sa_admins
from app.handlers.superadmin import broadcast as sa_broadcast
from app.handlers.superadmin import backup as sa_backup


def run_migrations() -> None:
    """Alembic migratsiyalarini bot ishga tushishidan oldin, runtime'da bajaradi.
    MUHIM: bu build vaqtida emas, konteyner haqiqatan ishga tushganda chaqiriladi —
    shu payt Railway'ning ichki tarmog'i (masalan postgres.railway.internal)
    allaqachon mavjud bo'ladi."""
    logger.info("Migratsiyalar ishga tushirilmoqda...")
    result = subprocess.run(
        [sys.executable, "-m", "alembic", "upgrade", "head"],
        check=False,
    )
    if result.returncode != 0:
        logger.error("Migratsiya bajarilmadi! Bot to'xtatilmoqda.")
        raise SystemExit(result.returncode)
    logger.info("Migratsiyalar muvaffaqiyatli yakunlandi.")


def create_dispatcher() -> Dispatcher:
    dp = Dispatcher(storage=MemoryStorage())

    # --- Middlewarelar (tartib muhim: avval session, keyin role) ---
    dp.update.middleware(DbSessionMiddleware())
    dp.update.middleware(RoleMiddleware())
    dp.message.middleware(ThrottlingMiddleware())

    # --- Routerlar ---
    dp.include_router(user_start.router)
    dp.include_router(user_captcha.router)
    dp.include_router(user_menu.router)

    dp.include_router(admin_panel.router)
    dp.include_router(admin_search.router)
    dp.include_router(admin_export.router)

    dp.include_router(sa_contest.router)
    dp.include_router(sa_channels.router)
    dp.include_router(sa_admins.router)
    dp.include_router(sa_broadcast.router)
    dp.include_router(sa_backup.router)

    return dp


async def on_startup(bot: Bot) -> None:
    if settings.USE_WEBHOOK:
        await bot.set_webhook(
            url=settings.webhook_url,
            drop_pending_updates=True,
            allowed_updates=["message", "callback_query"],
        )
        logger.info(f"Webhook o'rnatildi: {settings.webhook_url}")
    else:
        await bot.delete_webhook(drop_pending_updates=True)
        logger.info("Polling rejimida ishga tushmoqda")

    scheduler = setup_scheduler(bot)
    scheduler.start()
    logger.info("Scheduler ishga tushdi")


def main() -> None:
    run_migrations()

    bot = Bot(
        token=settings.BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    dp = create_dispatcher()
    dp.startup.register(on_startup)

    if settings.USE_WEBHOOK:
        app = web.Application()
        SimpleRequestHandler(dispatcher=dp, bot=bot).register(app, path=settings.WEBHOOK_PATH)
        setup_application(app, dp, bot=bot)
        logger.info(f"Webhook server ishga tushmoqda: {settings.WEBAPP_HOST}:{settings.WEBAPP_PORT}")
        web.run_app(app, host=settings.WEBAPP_HOST, port=settings.WEBAPP_PORT)
    else:
        asyncio.run(dp.start_polling(bot))


if __name__ == "__main__":
    main()
