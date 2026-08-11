"""Admin: reytingni Excel formatida eksport qilish."""
from __future__ import annotations

from aiogram import Router
from aiogram.types import BufferedInputFile, CallbackQuery
from sqlalchemy.ext.asyncio import AsyncSession

from app.filters.role_filter import RoleFilter
from app.services.contest_service import ContestService
from app.services.export_service import ExportService

router = Router(name="admin_export")
router.callback_query.filter(RoleFilter("admin"))


@router.callback_query(lambda c: c.data == "admin:export")
async def export_excel(callback: CallbackQuery, session: AsyncSession) -> None:
    contest_service = ContestService(session)
    contest = await contest_service.get_current_for_user()

    if not contest:
        await callback.answer("Hozircha aktiv konkurs mavjud emas.", show_alert=True)
        return

    await callback.answer("⏳ Excel tayyorlanmoqda...")

    export_service = ExportService(session)
    buffer = await export_service.export_leaderboard_to_excel(contest.id, contest.title)

    filename = f"reyting_{contest.id}.xlsx"
    await callback.message.answer_document(
        BufferedInputFile(buffer.read(), filename=filename),
        caption=f"📥 <b>{contest.title}</b> — to'liq reyting",
    )
