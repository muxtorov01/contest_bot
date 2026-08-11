"""Superadmin: qo'lda backup yaratish."""
from __future__ import annotations

from aiogram import Router, Bot
from aiogram.types import CallbackQuery

from app.filters.role_filter import RoleFilter
from app.keyboards.superadmin_kb import back_to_sa_kb
from app.services.backup_service import BackupService

router = Router(name="superadmin_backup")
router.callback_query.filter(RoleFilter("superadmin"))


@router.callback_query(lambda c: c.data == "sa:backup")
async def manual_backup(callback: CallbackQuery, bot: Bot) -> None:
    await callback.answer("⏳ Backup yaratilmoqda...")
    await callback.message.edit_text("⏳ Backup yaratilmoqda, biroz kuting...")

    backup_service = BackupService(bot)
    success = await backup_service.create_and_send_backup()

    if success:
        await callback.message.edit_text("✅ Backup muvaffaqiyatli yaratildi va yuborildi.", reply_markup=back_to_sa_kb())
    else:
        await callback.message.edit_text("❌ Backup yaratishda xato yuz berdi. Loglarni tekshiring.", reply_markup=back_to_sa_kb())
