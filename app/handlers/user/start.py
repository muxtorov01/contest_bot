"""/start komandasi: ro'yxatdan o'tkazish, referral ro'yxatga olish, captcha ko'rsatish."""
from __future__ import annotations

from html import escape

from aiogram import Router, Bot, F
from aiogram.filters import CommandStart, CommandObject
from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.keyboards.user_kb import main_menu_kb, subscribe_channels_kb
from app.repositories.user_repo import UserRepository
from app.services.contest_service import ContestService
from app.services.referral_service import ReferralService
from app.services.subscription_service import SubscriptionService
from app.utils.captcha_gen import generate_captcha
from app.utils.logger import logger

router = Router(name="user_start")


@router.message(CommandStart(deep_link=True))
@router.message(CommandStart())
async def cmd_start(
    message: Message, command: CommandObject, session: AsyncSession, bot: Bot, state: FSMContext
) -> None:
    user_repo = UserRepository(session)
    tg_user = message.from_user

    user, is_new = await user_repo.get_or_create(
        user_id=tg_user.id, username=tg_user.username, full_name=tg_user.full_name
    )

    # --- Referral parametrini o'qish ---
    payload = command.args
    contest_service = ContestService(session)
    contest = await contest_service.get_current_for_user()

    if payload and payload.isdigit() and contest:
        referrer_id = int(payload)
        if referrer_id != tg_user.id:
            referral_service = ReferralService(session, bot)
            await referral_service.register_referral_click(
                contest_id=contest.id, referrer_id=referrer_id, invited_id=tg_user.id
            )
        else:
            logger.info(f"O'zini o'zi refer qilishga urinish: {tg_user.id}")

    # --- Captcha bloklanganmi tekshirish ---
    if await user_repo.is_captcha_blocked(tg_user.id):
        await message.answer(
            "⛔️ Siz vaqtincha bloklangansiz. Iltimos, biroz vaqtdan so'ng qayta urinib ko'ring."
        )
        return

    if not user.is_captcha_verified:
        question, correct, kb = generate_captcha()
        # To'g'ri javob FAQAT serverda (FSM state) saqlanadi, callback_data'da emas.
        await state.update_data(captcha_answer=correct)
        safe_name = escape(tg_user.full_name or "")
        await message.answer(
            f"👋 Assalomu alaykum, {safe_name}!\n\n{question}",
            reply_markup=kb,
        )
        return

    # --- Captcha allaqachon tasdiqlangan bo'lsa, obunani tekshiramiz ---
    await _proceed_after_captcha(message, session, bot, contest)


async def _proceed_after_captcha(message: Message, session: AsyncSession, bot: Bot, contest) -> None:
    tg_user = message.from_user

    if not contest:
        await message.answer(
            "ℹ️ Hozircha aktiv konkurs mavjud emas. Yangi konkurs boshlanganda sizga xabar beramiz.",
            reply_markup=main_menu_kb(),
        )
        return

    subscription_service = SubscriptionService(session, bot)
    all_subscribed, missing = await subscription_service.check_all_subscriptions(tg_user.id, contest.id)

    if not all_subscribed:
        await message.answer(
            "📢 Konkursda ishtirok etish uchun quyidagi kanallarga obuna bo'ling, "
            "so'ngra <b>✅ Tekshirish</b> tugmasini bosing:",
            reply_markup=subscribe_channels_kb(missing),
        )
        return

    referral_service = ReferralService(session, bot)
    await referral_service.try_verify(contest.id, tg_user.id)

    await message.answer(
        f"✅ Xush kelibsiz!\n\n🎉 <b>{contest.title}</b> konkursida ishtirok etyapsiz.\n\n"
        "Quyidagi menyudan foydalaning:",
        reply_markup=main_menu_kb(),
    )
