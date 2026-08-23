"""Captcha javobini qayta ishlash va obuna tekshiruvi (✅ Tekshirish tugmasi)."""
from __future__ import annotations

from aiogram import Router, Bot
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.keyboards.user_kb import main_menu_kb, subscribe_channels_kb
from app.repositories.user_repo import UserRepository
from app.services.contest_service import ContestService
from app.services.referral_service import ReferralService
from app.services.subscription_service import SubscriptionService

router = Router(name="user_captcha")


@router.callback_query(lambda c: c.data and c.data.startswith("captcha:"))
async def process_captcha(callback: CallbackQuery, session: AsyncSession, bot: Bot, state: FSMContext) -> None:
    _, chosen = callback.data.split(":")
    data = await state.get_data()
    correct = data.get("captcha_answer")

    if correct is None:
        # State topilmadi (masalan eski/tugagan tugma) - qayta /start ni so'raymiz.
        await callback.answer("⏳ Captcha muddati tugagan. Iltimos, /start ni qayta bosing.", show_alert=True)
        return

    user_repo = UserRepository(session)
    tg_user = callback.from_user

    if int(chosen) == int(correct):
        await state.update_data(captcha_answer=None)
        await user_repo.set_captcha_verified(tg_user.id, True)
        await callback.message.edit_text("✅ Tasdiqlandi! Endi majburiy shartlarni tekshiramiz...")

        contest_service = ContestService(session)
        contest = await contest_service.get_current_for_user()

        if not contest:
            await callback.message.answer(
                "ℹ️ Hozircha aktiv konkurs mavjud emas.", reply_markup=main_menu_kb()
            )
            await callback.answer()
            return

        subscription_service = SubscriptionService(session, bot)
        all_subscribed, missing = await subscription_service.check_all_subscriptions(tg_user.id, contest.id)

        if not all_subscribed:
            await callback.message.answer(
                "📢 Konkursda ishtirok etish uchun quyidagi kanallarga obuna bo'ling, "
                "so'ngra <b>✅ Tekshirish</b> tugmasini bosing:",
                reply_markup=subscribe_channels_kb(missing),
            )
            await callback.answer()
            return

        referral_service = ReferralService(session, bot)
        await referral_service.try_verify(contest.id, tg_user.id)

        await callback.message.answer(
            f"🎉 Xush kelibsiz! <b>{contest.title}</b> konkursida ishtirok etyapsiz.",
            reply_markup=main_menu_kb(),
        )
        await callback.answer()
    else:
        fail_count = await user_repo.register_captcha_fail(
            tg_user.id, settings.CAPTCHA_MAX_ATTEMPTS, settings.CAPTCHA_BLOCK_SECONDS
        )
        if fail_count == 0:
            await state.update_data(captcha_answer=None)
            await callback.message.edit_text(
                f"❌ Noto'g'ri javob!\n\n⛔️ Siz {settings.CAPTCHA_BLOCK_SECONDS} soniyaga bloklandingiz. "
                "Keyin /start ni qayta bosing."
            )
        else:
            remaining = settings.CAPTCHA_MAX_ATTEMPTS - fail_count
            await callback.message.edit_text(
                f"❌ Noto'g'ri javob! Yana {remaining} ta urinish qoldi.\n\n"
                "Qayta urinish uchun /start ni bosing."
            )
        await callback.answer("Noto'g'ri javob", show_alert=True)


@router.callback_query(lambda c: c.data == "check_subscription")
async def check_subscription(callback: CallbackQuery, session: AsyncSession, bot: Bot) -> None:
    tg_user = callback.from_user
    contest_service = ContestService(session)
    contest = await contest_service.get_current_for_user()

    if not contest:
        await callback.message.edit_text("ℹ️ Hozircha aktiv konkurs mavjud emas.")
        await callback.answer()
        return

    subscription_service = SubscriptionService(session, bot)
    all_subscribed, missing = await subscription_service.check_all_subscriptions(tg_user.id, contest.id)

    if not all_subscribed:
        await callback.answer("❌ Siz hali barcha kanallarga obuna bo'lmagansiz!", show_alert=True)
        return

    referral_service = ReferralService(session, bot)
    verified = await referral_service.try_verify(contest.id, tg_user.id)

    await callback.message.edit_text(
        f"✅ Barcha shartlar bajarildi!\n\n🎉 <b>{contest.title}</b> konkursida ishtirok etyapsiz."
    )
    await callback.message.answer("Quyidagi menyudan foydalaning:", reply_markup=main_menu_kb())
    await callback.answer("Tabriklaymiz! ✅" if verified else "Obuna tasdiqlandi ✅")
