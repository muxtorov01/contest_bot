"""Admin: user qidirish va profilini ochish."""
from __future__ import annotations

from html import escape

from aiogram import Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession

from app.filters.role_filter import RoleFilter
from app.keyboards.admin_kb import back_to_admin_kb
from app.repositories.user_repo import UserRepository
from app.services.contest_service import ContestService
from app.services.rating_service import RatingService
from app.services.referral_service import ReferralService
from app.states.contest_states import SearchUserStates
from app.utils.text import format_dt

router = Router(name="admin_search")
router.message.filter(RoleFilter("admin"))
router.callback_query.filter(RoleFilter("admin"))


@router.callback_query(lambda c: c.data == "admin:search")
async def start_search(callback: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(SearchUserStates.waiting_query)
    await callback.message.edit_text(
        "🔍 Qidiruv uchun Telegram ID yoki username kiriting:", reply_markup=back_to_admin_kb()
    )
    await callback.answer()


@router.message(SearchUserStates.waiting_query)
async def process_search(message: Message, state: FSMContext, session: AsyncSession, bot) -> None:
    await state.clear()
    query = message.text.strip()

    user_repo = UserRepository(session)
    results = await user_repo.search(query, limit=10)

    if not results:
        await message.answer("❌ Hech narsa topilmadi.", reply_markup=back_to_admin_kb())
        return

    contest_service = ContestService(session)
    contest = await contest_service.get_current_for_user()
    rating_service = RatingService(session)
    referral_service = ReferralService(session, bot)

    for user in results:
        safe_username = escape(user.username) if user.username else None
        safe_full_name = escape(user.full_name) if user.full_name else None
        text_lines = [
            f"👤 <b>Profil</b>",
            f"ID: <code>{user.id}</code>",
            f"Username: @{safe_username}" if safe_username else "Username: —",
            f"F.I.O: {safe_full_name or '—'}",
            f"Captcha tasdiqlangan: {'✅' if user.is_captcha_verified else '❌'}",
            f"Bloklangan: {'✅' if user.is_blocked else '❌'}",
            f"Ro'yxatdan o'tgan: {format_dt(user.created_at)}",
        ]
        if contest:
            count = await referral_service.get_user_verified_count(contest.id, user.id)
            rank, _ = await rating_service.get_user_rank(contest.id, user.id)
            text_lines.append(f"🎯 Verified referral: {count}")
            text_lines.append(f"📍 O'rni: #{rank}" if rank else "📍 O'rni: reytingda emas")
        await message.answer("\n".join(text_lines), reply_markup=back_to_admin_kb())
