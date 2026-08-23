"""Broadcast (ommaviy xabar) yuborish logikasi."""
from __future__ import annotations

import asyncio

from aiogram import Bot
from aiogram.exceptions import TelegramForbiddenError, TelegramRetryAfter, TelegramAPIError
from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.user_repo import UserRepository
from app.utils.logger import logger

BROADCAST_CHUNK_SIZE = 25
BROADCAST_DELAY = 0.05  # so'rovlar orasidagi tanaffus (flood limitdan qochish uchun)


class BroadcastService:
    def __init__(self, session: AsyncSession, bot: Bot) -> None:
        self.session = session
        self.bot = bot
        self.user_repo = UserRepository(session)

    async def broadcast_text(self, text: str) -> tuple[int, int]:
        """Barcha faol (bloklanmagan) foydalanuvchilarga xabar yuboradi.
        Qaytaradi: (muvaffaqiyatli, muvaffaqiyatsiz)."""
        user_ids = await self.user_repo.all_active_ids()
        return await self.broadcast_to_ids(user_ids, text)

    async def broadcast_to_ids(self, user_ids: list[int], text: str) -> tuple[int, int]:
        """Berilgan ID lar ro'yxatidagi (masalan, konkurs ishtirokchilari)
        bloklanmagan foydalanuvchilarga xabar yuboradi.
        Qaytaradi: (muvaffaqiyatli, muvaffaqiyatsiz)."""
        user_ids = await self.user_repo.filter_active_ids(user_ids)
        success, failed = 0, 0

        for i in range(0, len(user_ids), BROADCAST_CHUNK_SIZE):
            chunk = user_ids[i : i + BROADCAST_CHUNK_SIZE]
            for user_id in chunk:
                try:
                    await self.bot.send_message(user_id, text)
                    success += 1
                except TelegramRetryAfter as e:
                    await asyncio.sleep(e.retry_after)
                    try:
                        await self.bot.send_message(user_id, text)
                        success += 1
                    except TelegramAPIError:
                        failed += 1
                except TelegramForbiddenError:
                    await self.user_repo.set_blocked(user_id, True)
                    failed += 1
                except TelegramAPIError as e:
                    logger.warning(f"Broadcast xatosi user={user_id}: {e}")
                    failed += 1
                await asyncio.sleep(BROADCAST_DELAY)

        logger.info(f"Broadcast tugadi: {success} muvaffaqiyatli, {failed} xato")
        return success, failed
