"""Admin panel: /admin komandasi va TOP 50."""
from __future__ import annotations

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from sqlalchemy.ext.asyncio import AsyncSession

from app.filters.role_filter import RoleFilter
from app.keyboards.admin_kb import admin_panel_kb, back_to_admin_kb
from app.services.contest_service import ContestService
from app.services.rating_service import RatingService

router = Router(name="admin_panel")
router.message.filter(RoleFilter("admin"))
router.callback_query.filter(RoleFilter("admin"))


@router.message(Command("admin"))
async def open_admin_panel(message: Message) -> None:
    await message.answer("👮 <b>Admin panel</b>", reply_markup=admin_panel_kb())


@router.callback_query(lambda c: c.data == "admin:panel")
async def back_to_panel(callback: CallbackQuery) -> None:
    await callback.message.edit_text("👮 <b>Admin panel</b>", reply_markup=admin_panel_kb())
    await callback.answer()


@router.callback_query(lambda c: c.data == "admin:top50")
async def top50(callback: CallbackQuery, session: AsyncSession) -> None:
    contest_service = ContestService(session)
    contest = await contest_service.get_current_for_user()

    if not contest:
        await callback.answer("Hozircha aktiv konkurs mavjud emas.", show_alert=True)
        return

    rating_service = RatingService(session)
    top_list = await rating_service.get_top_50(contest.id, for_admin=True)

    if not top_list:
        text = "🏆 <b>TOP 50</b>\n\nHozircha hech kim ball to'plamagan."
    else:
        lines = ["🏆 <b>TOP 50</b>\n"]
        for entry in top_list:
            lines.append(f"{entry['rank']}. {entry['name']} — {entry['count']}")
        text = "\n".join(lines)

    # Telegram xabar uzunligi cheklovi uchun bo'lib yuboramiz
    if len(text) > 4000:
        for i in range(0, len(text), 4000):
            await callback.message.answer(text[i : i + 4000])
    else:
        await callback.message.answer(text)
    await callback.answer()
