"""Superadmin: admin qo'shish/o'chirish."""
from __future__ import annotations

from aiogram import Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message
from sqlalchemy.ext.asyncio import AsyncSession

from app.filters.role_filter import RoleFilter
from app.keyboards.superadmin_kb import admins_management_kb, back_to_sa_kb
from app.models.admin import AdminRole
from app.repositories.admin_repo import AdminRepository
from app.states.contest_states import AddAdminStates

router = Router(name="superadmin_admins")
router.message.filter(RoleFilter("superadmin"))
router.callback_query.filter(RoleFilter("superadmin"))


@router.callback_query(lambda c: c.data == "sa:admins")
async def list_admins(callback: CallbackQuery, session: AsyncSession) -> None:
    admin_repo = AdminRepository(session)
    admins = await admin_repo.list_all()
    text = "👮 <b>Adminlar ro'yxati</b>\n\n" + (
        "\n".join(f"• {a.id} — {a.role.value}" for a in admins) if admins else "Hozircha admin yo'q."
    )
    await callback.message.edit_text(text, reply_markup=admins_management_kb(admins))
    await callback.answer()


@router.callback_query(lambda c: c.data == "sa:add_admin")
async def add_admin_start(callback: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(AddAdminStates.waiting_user_id)
    await callback.message.edit_text("👤 Yangi admin Telegram ID'sini kiriting:", reply_markup=back_to_sa_kb())
    await callback.answer()


@router.message(AddAdminStates.waiting_user_id)
async def add_admin_id(message: Message, state: FSMContext) -> None:
    if not message.text.strip().isdigit():
        await message.answer("❌ Telegram ID faqat raqamlardan iborat bo'lishi kerak.")
        return
    await state.update_data(user_id=int(message.text.strip()))
    await state.set_state(AddAdminStates.waiting_role)

    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="Admin", callback_data="sa:role:admin"),
                InlineKeyboardButton(text="Superadmin", callback_data="sa:role:superadmin"),
            ]
        ]
    )
    await message.answer("🎚 Rolni tanlang:", reply_markup=kb)


@router.callback_query(AddAdminStates.waiting_role, lambda c: c.data.startswith("sa:role:"))
async def add_admin_role(callback: CallbackQuery, state: FSMContext, session: AsyncSession) -> None:
    role_str = callback.data.split(":")[-1]
    role = AdminRole.SUPERADMIN if role_str == "superadmin" else AdminRole.ADMIN

    data = await state.get_data()
    await state.clear()

    admin_repo = AdminRepository(session)
    admin = await admin_repo.add(data["user_id"], role, callback.from_user.id)

    await callback.message.edit_text(
        f"✅ Admin qo'shildi: <code>{admin.id}</code> ({admin.role.value})",
        reply_markup=back_to_sa_kb(),
    )
    await callback.answer()


@router.callback_query(lambda c: c.data.startswith("sa:remove_admin:"))
async def remove_admin(callback: CallbackQuery, session: AsyncSession) -> None:
    user_id = int(callback.data.split(":")[-1])
    admin_repo = AdminRepository(session)
    await admin_repo.remove(user_id)
    await callback.answer("✅ Admin o'chirildi")
    await list_admins(callback, session)
