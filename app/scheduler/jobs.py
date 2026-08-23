"""APScheduler orqali background vazifalar.

Har 1 daqiqada:
    - konkurslarni avtomatik start/end qilish va tegishli xabarnomalarni yuborish
Har N soatda:
    - obunani qayta tekshirish, bekor referrallarni ayirish
Har 24 soatda:
    - PostgreSQL backup yaratish va Telegram kanaliga yuborish
"""
from __future__ import annotations

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from aiogram import Bot

from app.config import settings
from app.database import get_session
from app.services.backup_service import BackupService
from app.services.contest_service import ContestService
from app.services.notification_service import ContestNotificationService
from app.services.referral_service import ReferralService
from app.utils.logger import logger


async def job_contest_auto_transition(bot: Bot) -> None:
    """scheduled -> active, active -> ended o'tishlarni bajaradi va tegishli xabarnomalarni yuboradi."""
    async with get_session() as session:
        contest_service = ContestService(session)
        started, ended = await contest_service.auto_transition()

        notification_service = ContestNotificationService(session, bot)

        for contest in started:
            logger.info(f"Konkurs avtomatik boshlandi: {contest.title}")
            success, failed = await notification_service.notify_contest_started(contest)
            logger.info(f"Avtomatik start xabari: id={contest.id} success={success} failed={failed}")

        for contest in ended:
            logger.info(f"Konkurs avtomatik tugadi: {contest.title}")
            success, failed = await notification_service.notify_contest_ended(contest)
            logger.info(f"Avtomatik tugash xabari: id={contest.id} success={success} failed={failed}")


async def job_recheck_subscriptions(bot: Bot) -> None:
    """Obunani qayta tekshiradi, chiqib ketganlarning referralini bekor qiladi."""
    async with get_session() as session:
        contest_service = ContestService(session)
        contest = await contest_service.get_active()
        if not contest:
            return
        referral_service = ReferralService(session, bot)
        cancelled = await referral_service.recheck_and_cancel_unsubscribed(contest.id)
        if cancelled:
            logger.info(f"Obunadan chiqib ketganlar uchun bekor qilingan referrallar: {cancelled}")


async def job_create_backup(bot: Bot) -> None:
    """PostgreSQL backup yaratadi va yopiq kanalga yuboradi."""
    backup_service = BackupService(bot)
    await backup_service.create_and_send_backup()


def setup_scheduler(bot: Bot) -> AsyncIOScheduler:
    scheduler = AsyncIOScheduler(timezone=settings.TIMEZONE)

    scheduler.add_job(
        job_contest_auto_transition,
        trigger=IntervalTrigger(minutes=1),
        args=[bot],
        id="contest_auto_transition",
        replace_existing=True,
    )

    scheduler.add_job(
        job_recheck_subscriptions,
        trigger=IntervalTrigger(hours=settings.SUBSCRIPTION_RECHECK_INTERVAL_HOURS),
        args=[bot],
        id="recheck_subscriptions",
        replace_existing=True,
    )

    scheduler.add_job(
        job_create_backup,
        trigger=IntervalTrigger(hours=settings.BACKUP_INTERVAL_HOURS),
        args=[bot],
        id="create_backup",
        replace_existing=True,
    )

    return scheduler
