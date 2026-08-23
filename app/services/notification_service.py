"""Konkurs boshlanishi/tugashi haqida xabarnoma yuborish logikasi.

- Konkurs BOSHLANGANDA: botdagi barcha foydalanuvchilarga xabar boradi.
- Konkurs TUGAGANDA (yoki to'xtatilganda): faqat shu konkursda ishtirok etgan
  (referrer yoki taklif qilingan bo'lgan) foydalanuvchilarga TOP 20 natija bilan xabar boradi.
"""
from __future__ import annotations

from html import escape

from aiogram import Bot
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.contest import Contest
from app.repositories.referral_repo import ReferralRepository
from app.services.broadcast_service import BroadcastService
from app.services.rating_service import RatingService
from app.utils.logger import logger
from app.utils.text import format_dt


class ContestNotificationService:
    def __init__(self, session: AsyncSession, bot: Bot) -> None:
        self.session = session
        self.bot = bot
        self.broadcast_service = BroadcastService(session, bot)
        self.rating_service = RatingService(session)
        self.referral_repo = ReferralRepository(session)

    async def notify_contest_started(self, contest: Contest) -> tuple[int, int]:
        """Botdagi HAMMAGA konkurs boshlanganligi haqida xabar yuboradi."""
        text = (
            "🎉 <b>Yangi konkurs boshlandi!</b>\n\n"
            f"📌 <b>{escape(contest.title)}</b>\n\n"
            f"{escape(contest.description)}\n\n"
            f"⏰ Tugash vaqti: {format_dt(contest.end_at)}\n\n"
            "🔗 «Referral havolam» tugmasi orqali havolangizni oling va do'stlaringizni "
            "taklif qilib, sovg'a yutib olish imkoniyatini oshiring!"
        )
        success, failed = await self.broadcast_service.broadcast_text(text)
        logger.info(
            f"Konkurs boshlanishi haqida xabar yuborildi: id={contest.id} "
            f"success={success} failed={failed}"
        )
        return success, failed

    async def notify_contest_ended(self, contest: Contest) -> tuple[int, int]:
        """Faqat shu konkursda ISHTIROK ETGANLARGA konkurs tugaganligi va TOP 20 ni yuboradi."""
        participant_ids = await self.referral_repo.participant_ids(contest.id)
        if not participant_ids:
            logger.info(f"Konkurs id={contest.id} tugadi, lekin ishtirokchi topilmadi.")
            return 0, 0

        top_list = await self.rating_service.get_top(contest.id, limit=20)
        text = self.rating_service.format_contest_ended_message(contest, top_list)

        success, failed = await self.broadcast_service.broadcast_to_ids(participant_ids, text)
        logger.info(
            f"Konkurs yakuni haqida xabar yuborildi: id={contest.id} "
            f"success={success} failed={failed}"
        )
        return success, failed
