"""Majburiy kanallarga obuna tekshiruvi bilan bog'liq logika."""
from __future__ import annotations

from aiogram import Bot
from aiogram.exceptions import TelegramAPIError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.channel import RequiredChannel
from app.repositories.channel_repo import ChannelRepository
from app.utils.logger import logger

# Ushbu statuslar "obuna bo'lgan" deb hisoblanadi
SUBSCRIBED_STATUSES = {"member", "administrator", "creator"}


class SubscriptionService:
    def __init__(self, session: AsyncSession, bot: Bot) -> None:
        self.session = session
        self.bot = bot
        self.channel_repo = ChannelRepository(session)

    async def get_required_channels(self, contest_id: int) -> list[RequiredChannel]:
        return await self.channel_repo.list_active_for_contest(contest_id)

    async def is_subscribed(self, user_id: int, channel: RequiredChannel) -> bool:
        try:
            member = await self.bot.get_chat_member(chat_id=channel.chat_id, user_id=user_id)
            return member.status in SUBSCRIBED_STATUSES
        except TelegramAPIError as e:
            logger.warning(f"Obuna tekshirishda xato (chat={channel.chat_id}, user={user_id}): {e}")
            # Bot kanalda admin bo'lmasa yoki xato bo'lsa - xavfsizlik uchun False qaytaramiz
            return False

    async def check_all_subscriptions(self, user_id: int, contest_id: int) -> tuple[bool, list[RequiredChannel]]:
        """Barcha majburiy kanallarga obuna bo'lganmi tekshiradi.
        Qaytaradi: (barchasiga_obuna_bo'lganmi, obuna_bo'lmagan_kanallar_ro'yxati)"""
        channels = await self.get_required_channels(contest_id)
        not_subscribed: list[RequiredChannel] = []
        for channel in channels:
            if not await self.is_subscribed(user_id, channel):
                not_subscribed.append(channel)
        return len(not_subscribed) == 0, not_subscribed

    async def verify_bot_is_admin(self, channel: RequiredChannel) -> bool:
        """Bot shu kanalda admin ekanligini tekshiradi (kanal biriktirilganda chaqiriladi)."""
        try:
            me = await self.bot.get_me()
            member = await self.bot.get_chat_member(chat_id=channel.chat_id, user_id=me.id)
            return member.status in {"administrator", "creator"}
        except TelegramAPIError as e:
            logger.error(f"Bot kanal={channel.chat_id} da admin emas yoki xato: {e}")
            return False
