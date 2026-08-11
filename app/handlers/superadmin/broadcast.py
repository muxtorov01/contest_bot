"""Superadmin: barcha foydalanuvchilarga xabar yuborish (broadcast)."""
from __future__ import annotations

from aiogram import Router, Bot
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession

from app.filters.role_filter import RoleFilter
from app.keyboards.superadmin_kb import back_to_sa_kb, confirm_kb
from app.services.broadcast_service import BroadcastService
from app.states.contest_states import BroadcastStates

router = Router(name="superadmin_broadcast")
router.message.filter(RoleFilter("superadmin"))
router.callback_query.filter(RoleFilter("superadmin"))


@router.callback_query(lambda c: c.data == "sa:broadcast")
async def broadcast_start(callback: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(BroadcastStates.waiting_text)
    await callback.message.edit_text(
        "📢 Barcha foydalanuvchilarga yuboriladigan xabar matnini kiriting:",
        reply_markup=back_to_sa_kb(),
    )
    await callback.answer()


@router.message(BroadcastStates.waiting_text)
async def broadcast_preview(message: Message, state: FSMContext) -> None:
    await state.update_data(text=message.html_text)
    await state.set_state(BroadcastStates.confirm)
    await message.answer(
        f"👀 <b>Ko'rinishi:</b>\n\n{message.html_text}\n\n---\nYuborishni tasdiqlaysizmi?",
        reply_markup=confirm_kb("sa:confirm_broadcast", "sa:cancel_broadcast"),
    )


@router.callback_query(lambda c: c.data == "sa:cancel_broadcast")
async def broadcast_cancel(callback: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await callback.message.edit_text("❌ Bekor qilindi.", reply_markup=back_to_sa_kb())
    await callback.answer()


@router.callback_query(lambda c: c.data == "sa:confirm_broadcast")
async def broadcast_send(callback: CallbackQuery, state: FSMContext, session: AsyncSession, bot: Bot) -> None:
    data = await state.get_data()
    await state.clear()

    await callback.message.edit_text("⏳ Xabar yuborilmoqda, bu biroz vaqt olishi mumkin...")

    broadcast_service = BroadcastService(session, bot)
    success, failed = await broadcast_service.broadcast_text(data["text"])

    await callback.message.answer(
        f"✅ Broadcast yakunlandi!\n\n📤 Yuborildi: {success}\n❌ Xato: {failed}",
        reply_markup=back_to_sa_kb(),
    )
    await callback.answer()
