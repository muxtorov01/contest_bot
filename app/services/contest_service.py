"""Konkurs bilan bog'liq biznes logika."""
from __future__ import annotations

import datetime as dt

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.contest import Contest, ContestStatus
from app.repositories.contest_repo import ContestRepository
from app.utils.logger import logger


class ContestAlreadyExistsError(Exception):
    """Allaqachon scheduled yoki active konkurs mavjud bo'lsa ko'tariladi."""


class ContestService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.repo = ContestRepository(session)

    async def create_contest(
        self,
        title: str,
        description: str,
        start_at: dt.datetime,
        end_at: dt.datetime,
        created_by: int,
    ) -> Contest:
        """Faqat 1 ta aktiv/rejalashtirilgan konkurs bo'lishi shart."""
        existing = await self.repo.get_scheduled_or_active()
        if existing:
            raise ContestAlreadyExistsError(
                f"Allaqachon '{existing.title}' nomli konkurs mavjud ({existing.status.value})."
            )
        if end_at <= start_at:
            raise ValueError("Tugash vaqti boshlanish vaqtidan keyin bo'lishi kerak.")
        contest = await self.repo.create(title, description, start_at, end_at, created_by)
        logger.info(f"Yangi konkurs yaratildi: {contest.title} (id={contest.id})")
        return contest

    async def start_now(self, contest_id: int) -> None:
        await self.repo.update_status(contest_id, ContestStatus.ACTIVE)
        contest = await self.repo.get(contest_id)
        if contest:
            contest.start_at = dt.datetime.now(dt.timezone.utc)
        logger.info(f"Konkurs qo'lda boshlandi: id={contest_id}")

    async def stop_now(self, contest_id: int) -> None:
        await self.repo.update_status(contest_id, ContestStatus.STOPPED)
        logger.info(f"Konkurs qo'lda to'xtatildi: id={contest_id}")

    async def reschedule(
        self, contest_id: int, start_at: dt.datetime | None, end_at: dt.datetime | None
    ) -> None:
        await self.repo.update_schedule(contest_id, start_at, end_at)
        logger.info(f"Konkurs vaqti o'zgartirildi: id={contest_id}")

    async def get_active(self) -> Contest | None:
        return await self.repo.get_active()

    async def get_current_for_user(self) -> Contest | None:
        """Foydalanuvchiga ko'rsatiladigan joriy konkurs (active ustuvor)."""
        active = await self.repo.get_active()
        if active:
            return active
        return None

    async def list_archive(self, limit: int = 20) -> list[Contest]:
        return await self.repo.list_archive(limit)

    async def auto_transition(self) -> tuple[list[Contest], list[Contest]]:
        """Scheduled -> Active va Active -> Ended avtomatik o'tishlarni bajaradi.
        Scheduler tomonidan chaqiriladi. (started, ended) tuple qaytaradi."""
        now = dt.datetime.now(dt.timezone.utc)
        started: list[Contest] = []
        ended: list[Contest] = []

        for contest in await self.repo.due_to_start(now):
            await self.repo.update_status(contest.id, ContestStatus.ACTIVE)
            started.append(contest)
            logger.info(f"Konkurs avtomatik boshlandi: {contest.title}")

        for contest in await self.repo.due_to_end(now):
            await self.repo.update_status(contest.id, ContestStatus.ENDED)
            ended.append(contest)
            logger.info(f"Konkurs avtomatik tugadi: {contest.title}")

        return started, ended
