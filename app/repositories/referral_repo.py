"""Referral bilan bog'liq DB operatsiyalari."""
from __future__ import annotations

import datetime as dt

from sqlalchemy import select, func, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.referral import Referral, ReferralStatus


class ReferralRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_by_invited(self, invited_id: int) -> Referral | None:
        """Har bir invited_id uchun faqat bitta referral bo'ladi
        (birinchi referral saqlanadi - UniqueConstraint)."""
        stmt = select(Referral).where(Referral.invited_id == invited_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def create_pending(self, contest_id: int, referrer_id: int, invited_id: int) -> Referral | None:
        """Yangi pending referral yaratadi. Agar invited_id allaqachon mavjud bo'lsa None qaytaradi."""
        existing = await self.get_by_invited(invited_id)
        if existing:
            return None
        if referrer_id == invited_id:
            return None  # o'zini o'zi refer qilish taqiqlangan
        referral = Referral(
            contest_id=contest_id,
            referrer_id=referrer_id,
            invited_id=invited_id,
            status=ReferralStatus.PENDING,
        )
        self.session.add(referral)
        await self.session.flush()
        return referral

    async def mark_verified(self, referral_id: int) -> None:
        referral = await self.session.get(Referral, referral_id)
        if referral and referral.status != ReferralStatus.VERIFIED:
            referral.status = ReferralStatus.VERIFIED
            referral.verified_at = dt.datetime.now(dt.timezone.utc)

    async def mark_cancelled(self, referral_id: int) -> None:
        referral = await self.session.get(Referral, referral_id)
        if referral and referral.status == ReferralStatus.VERIFIED:
            referral.status = ReferralStatus.CANCELLED
            referral.cancelled_at = dt.datetime.now(dt.timezone.utc)

    async def count_verified(self, contest_id: int, referrer_id: int) -> int:
        stmt = select(func.count(Referral.id)).where(
            Referral.contest_id == contest_id,
            Referral.referrer_id == referrer_id,
            Referral.status == ReferralStatus.VERIFIED,
        )
        result = await self.session.execute(stmt)
        return result.scalar_one()

    async def leaderboard(self, contest_id: int, limit: int = 20) -> list[tuple[int, int]]:
        """(referrer_id, verified_count) ro'yxatini ball bo'yicha kamayish tartibida qaytaradi."""
        stmt = (
            select(Referral.referrer_id, func.count(Referral.id).label("cnt"))
            .where(Referral.contest_id == contest_id, Referral.status == ReferralStatus.VERIFIED)
            .group_by(Referral.referrer_id)
            .order_by(func.count(Referral.id).desc())
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return [(row.referrer_id, row.cnt) for row in result.all()]

    async def full_ranking(self, contest_id: int) -> list[tuple[int, int]]:
        """Barcha referrerlarni ball bo'yicha tartiblab qaytaradi (o'rinni aniqlash uchun)."""
        stmt = (
            select(Referral.referrer_id, func.count(Referral.id).label("cnt"))
            .where(Referral.contest_id == contest_id, Referral.status == ReferralStatus.VERIFIED)
            .group_by(Referral.referrer_id)
            .order_by(func.count(Referral.id).desc())
        )
        result = await self.session.execute(stmt)
        return [(row.referrer_id, row.cnt) for row in result.all()]

    async def verified_referrals_by_referrer(self, contest_id: int) -> list[Referral]:
        """Bekor qilinishi mumkin bo'lgan (obuna qayta tekshiruvi uchun) VERIFIED referrallar."""
        stmt = select(Referral).where(
            Referral.contest_id == contest_id, Referral.status == ReferralStatus.VERIFIED
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def pending_referrals(self, contest_id: int) -> list[Referral]:
        stmt = select(Referral).where(
            Referral.contest_id == contest_id, Referral.status == ReferralStatus.PENDING
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
