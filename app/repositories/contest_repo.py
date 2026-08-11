"""Contest bilan bog'liq DB operatsiyalari."""
from __future__ import annotations

import datetime as dt

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.contest import Contest, ContestStatus


class ContestRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get(self, contest_id: int) -> Contest | None:
        return await self.session.get(Contest, contest_id)

    async def get_active(self) -> Contest | None:
        stmt = select(Contest).where(Contest.status == ContestStatus.ACTIVE)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_scheduled_or_active(self) -> Contest | None:
        """Faqat 1 ta aktiv konkurs bo'lishi kerak bo'lgani uchun,
        yangi konkurs yaratishdan oldin tekshiriladi."""
        stmt = select(Contest).where(
            Contest.status.in_([ContestStatus.SCHEDULED, ContestStatus.ACTIVE])
        )
        result = await self.session.execute(stmt)
        return result.scalars().first()

    async def create(
        self,
        title: str,
        description: str,
        start_at: dt.datetime,
        end_at: dt.datetime,
        created_by: int,
    ) -> Contest:
        contest = Contest(
            title=title,
            description=description,
            start_at=start_at,
            end_at=end_at,
            created_by=created_by,
            status=ContestStatus.SCHEDULED,
        )
        self.session.add(contest)
        await self.session.flush()
        return contest

    async def update_status(self, contest_id: int, status: ContestStatus) -> None:
        contest = await self.get(contest_id)
        if contest:
            contest.status = status

    async def update_schedule(
        self, contest_id: int, start_at: dt.datetime | None, end_at: dt.datetime | None
    ) -> None:
        contest = await self.get(contest_id)
        if not contest:
            return
        if start_at:
            contest.start_at = start_at
        if end_at:
            contest.end_at = end_at

    async def list_archive(self, limit: int = 20) -> list[Contest]:
        stmt = (
            select(Contest)
            .where(Contest.status.in_([ContestStatus.ENDED, ContestStatus.STOPPED]))
            .order_by(Contest.end_at.desc())
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def due_to_start(self, now: dt.datetime) -> list[Contest]:
        stmt = select(Contest).where(
            Contest.status == ContestStatus.SCHEDULED, Contest.start_at <= now
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def due_to_end(self, now: dt.datetime) -> list[Contest]:
        stmt = select(Contest).where(
            Contest.status == ContestStatus.ACTIVE, Contest.end_at <= now
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
