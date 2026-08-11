"""Referral tizimi biznes logikasi."""
from __future__ import annotations

from aiogram import Bot
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.referral import ReferralStatus
from app.repositories.referral_repo import ReferralRepository
from app.repositories.user_repo import UserRepository
from app.services.subscription_service import SubscriptionService
from app.utils.logger import logger


class ReferralService:
    def __init__(self, session: AsyncSession, bot: Bot) -> None:
        self.session = session
        self.bot = bot
        self.referral_repo = ReferralRepository(session)
        self.user_repo = UserRepository(session)
        self.subscription_service = SubscriptionService(session, bot)

    async def register_referral_click(self, contest_id: int, referrer_id: int, invited_id: int) -> bool:
        """Referral havolasi orqali kirilganda PENDING referral yozadi.
        Qaytaradi: yaratildimi (False bo'lsa - o'zini o'zi refer qilish yoki allaqachon mavjud)."""
        if referrer_id == invited_id:
            logger.info(f"O'zini o'zi refer qilishga urinish: {invited_id}")
            return False
        referral = await self.referral_repo.create_pending(contest_id, referrer_id, invited_id)
        return referral is not None

    async def try_verify(self, contest_id: int, invited_id: int) -> bool:
        """Captcha + barcha kanallarga obuna tasdiqlansa referralni VERIFIED qiladi.
        Qaytaradi: verified bo'ldimi."""
        referral = await self.referral_repo.get_by_invited(invited_id)
        if not referral or referral.status != ReferralStatus.PENDING:
            return False
        if referral.contest_id != contest_id:
            return False

        user = await self.user_repo.get(invited_id)
        if not user or not user.is_captcha_verified:
            return False

        all_subscribed, _ = await self.subscription_service.check_all_subscriptions(invited_id, contest_id)
        if not all_subscribed:
            return False

        await self.referral_repo.mark_verified(referral.id)
        logger.info(f"Referral VERIFIED: referrer={referral.referrer_id} invited={invited_id}")
        return True

    async def recheck_and_cancel_unsubscribed(self, contest_id: int) -> int:
        """Har soatlik background vazifa: VERIFIED referrallarni qayta tekshiradi,
        agar invited user endi kanallarga obuna bo'lmasa - referralni CANCELLED qiladi
        va referrerdan ball avtomatik kamayadi (chunki ball VERIFIED count'dan hisoblanadi)."""
        cancelled_count = 0
        verified_referrals = await self.referral_repo.verified_referrals_by_referrer(contest_id)
        for referral in verified_referrals:
            all_subscribed, _ = await self.subscription_service.check_all_subscriptions(
                referral.invited_id, contest_id
            )
            if not all_subscribed:
                await self.referral_repo.mark_cancelled(referral.id)
                cancelled_count += 1
                logger.info(
                    f"Referral bekor qilindi (obunadan chiqib ketgan): "
                    f"referrer={referral.referrer_id} invited={referral.invited_id}"
                )
        return cancelled_count

    async def get_user_verified_count(self, contest_id: int, user_id: int) -> int:
        return await self.referral_repo.count_verified(contest_id, user_id)
