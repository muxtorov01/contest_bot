"""Majburiy kanallar bilan bog'liq DB operatsiyalari."""
from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.channel import RequiredChannel


class ChannelRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get(self, channel_id: int) -> RequiredChannel | None:
        return await self.session.get(RequiredChannel, channel_id)

    async def list_active_for_contest(self, contest_id: int) -> list[RequiredChannel]:
        stmt = select(RequiredChannel).where(
            RequiredChannel.contest_id == contest_id, RequiredChannel.is_active.is_(True)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def add(
        self,
        contest_id: int,
        chat_id: int,
        title: str,
        username: str | None = None,
        invite_link: str | None = None,
    ) -> RequiredChannel:
        channel = RequiredChannel(
            contest_id=contest_id,
            chat_id=chat_id,
            title=title,
            username=username,
            invite_link=invite_link,
        )
        self.session.add(channel)
        await self.session.flush()
        return channel

    async def remove(self, channel_id: int) -> None:
        channel = await self.get(channel_id)
        if channel:
            channel.is_active = False
