"""Superadmin: konkurs yaratish, boshlash, tugatish, vaqtini o'zgartirish, arxiv."""
from __future__ import annotations

import datetime as dt

from aiogram import Bot, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession

from app.filters.role_filter import RoleFilter
from app.keyboards.superadmin_kb import (
    superadmin_panel_kb,
    confirm_kb,
    back_to_sa_kb,
)
from app.services.contest_service import ContestAlreadyExistsError, ContestService
from app.services.notification_service import ContestNotificationService
from app.states.contest_states import CreateContestStates, RescheduleContestStates
from app.utils.text import contest_status_uz, format_dt

router = Router(name="superadmin_contest")
router.message.filter(RoleFilter("superadmin"))
router.callback_query.filter(RoleFilter("superadmin"))

DATETIME_FORMAT = "%Y-%m-%d %H:%M"


@router.message(Command("superadmin"))
async def open_sa_panel(message: Message) -> None:
    await message.answer("🛠 <b>Superadmin panel</b>", reply_markup=superadmin_panel_kb())


@router.callback_query(lambda c: c.data == "sa:panel")
async def back_to_panel(callback: CallbackQuery) -> None:
    await callback.message.edit_text("🛠 <b>Superadmin panel</b>", reply_markup=superadmin_panel_kb())
    await callback.answer()


# ---------- Konkurs yaratish (FSM) ----------

@router.callback_query(lambda c: c.data == "sa:create_contest")
async def create_contest_start(callback: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(CreateContestStates.title)
    await callback.message.edit_text("📝 Konkurs nomini kiriting:", reply_markup=back_to_sa_kb())
    await callback.answer()


@router.message(CreateContestStates.title)
async def create_contest_title(message: Message, state: FSMContext) -> None:
    await state.update_data(title=message.text.strip())
    await state.set_state(CreateContestStates.description)
    await message.answer("📝 Konkurs tavsifini kiriting:")


@router.message(CreateContestStates.description)
async def create_contest_description(message: Message, state: FSMContext) -> None:
    await state.update_data(description=message.text.strip())
    await state.set_state(CreateContestStates.start_at)
    await message.answer(
        f"⏰ Boshlanish vaqtini kiriting (format: <code>{DATETIME_FORMAT}</code>):\n"
        f"Masalan: <code>2026-08-15 09:00</code>"
    )


@router.message(CreateContestStates.start_at)
async def create_contest_start_at(message: Message, state: FSMContext) -> None:
    try:
        start_at = dt.datetime.strptime(message.text.strip(), DATETIME_FORMAT).replace(tzinfo=dt.timezone.utc)
    except ValueError:
        await message.answer(f"❌ Noto'g'ri format! Masalan: <code>2026-08-15 09:00</code>")
        return
    await state.update_data(start_at=start_at.isoformat())
    await state.set_state(CreateContestStates.end_at)
    await message.answer(f"⏰ Tugash vaqtini kiriting (format: <code>{DATETIME_FORMAT}</code>):")


@router.message(CreateContestStates.end_at)
async def create_contest_end_at(message: Message, state: FSMContext) -> None:
    try:
        end_at = dt.datetime.strptime(message.text.strip(), DATETIME_FORMAT).replace(tzinfo=dt.timezone.utc)
    except ValueError:
        await message.answer(f"❌ Noto'g'ri format! Masalan: <code>2026-08-20 18:00</code>")
        return

    data = await state.update_data(end_at=end_at.isoformat())
    start_at = dt.datetime.fromisoformat(data["start_at"])

    await state.set_state(CreateContestStates.confirm)
    text = (
        "📋 <b>Konkurs ma'lumotlarini tasdiqlang:</b>\n\n"
        f"📌 Nomi: {data['title']}\n"
        f"📝 Tavsif: {data['description']}\n"
        f"⏰ Boshlanish: {format_dt(start_at)}\n"
        f"⏰ Tugash: {format_dt(end_at)}"
    )
    await message.answer(text, reply_markup=confirm_kb("sa:confirm_create", "sa:cancel_create"))


@router.callback_query(lambda c: c.data == "sa:cancel_create")
async def cancel_create(callback: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await callback.message.edit_text("❌ Bekor qilindi.", reply_markup=superadmin_panel_kb())
    await callback.answer()


@router.callback_query(lambda c: c.data == "sa:confirm_create")
async def confirm_create(callback: CallbackQuery, state: FSMContext, session: AsyncSession) -> None:
    data = await state.get_data()
    await state.clear()

    contest_service = ContestService(session)
    try:
        contest = await contest_service.create_contest(
            title=data["title"],
            description=data["description"],
            start_at=dt.datetime.fromisoformat(data["start_at"]),
            end_at=dt.datetime.fromisoformat(data["end_at"]),
            created_by=callback.from_user.id,
        )
    except (ContestAlreadyExistsError, ValueError) as e:
        await callback.message.edit_text(f"❌ Xato: {e}", reply_markup=superadmin_panel_kb())
        await callback.answer()
        return

    await callback.message.edit_text(
        f"✅ Konkurs yaratildi: <b>{contest.title}</b>\n\n"
        "Endi majburiy kanallarni biriktiring: 📡 Majburiy kanallar bo'limidan.",
        reply_markup=superadmin_panel_kb(),
    )
    await callback.answer()


# ---------- Boshlash / Tugatish ----------

@router.callback_query(lambda c: c.data == "sa:start_now")
async def start_now(callback: CallbackQuery, session: AsyncSession, bot: Bot) -> None:
    from app.repositories.contest_repo import ContestRepository

    contest_repo = ContestRepository(session)
    contest = await contest_repo.get_scheduled_or_active()

    if not contest:
        await callback.answer("Rejalashtirilgan konkurs topilmadi.", show_alert=True)
        return

    contest_service = ContestService(session)
    await contest_service.start_now(contest.id)
    await callback.message.edit_text(
        f"▶️ Konkurs boshlandi: <b>{contest.title}</b>\n\n⏳ Foydalanuvchilarga xabar yuborilmoqda...",
        reply_markup=superadmin_panel_kb(),
    )
    await callback.answer()

    # Botdagi HAMMAGA konkurs boshlanganligi haqida xabar yuboriladi.
    notification_service = ContestNotificationService(session, bot)
    success, failed = await notification_service.notify_contest_started(contest)
    await callback.message.answer(
        f"📣 Konkurs boshlanishi haqida xabar yuborildi.\n📤 Yuborildi: {success}\n❌ Xato: {failed}"
    )


@router.callback_query(lambda c: c.data == "sa:stop_now")
async def stop_now(callback: CallbackQuery, session: AsyncSession, bot: Bot) -> None:
    contest_service = ContestService(session)
    contest = await contest_service.get_active()

    if not contest:
        await callback.answer("Aktiv konkurs topilmadi.", show_alert=True)
        return

    await contest_service.stop_now(contest.id)
    await callback.message.edit_text(
        f"⏹ Konkurs to'xtatildi: <b>{contest.title}</b>\n\n⏳ Ishtirokchilarga natijalar yuborilmoqda...",
        reply_markup=superadmin_panel_kb(),
    )
    await callback.answer()

    # Konkurs tugaganligi va TOP 20 natijasi faqat ishtirokchilarga yuboriladi.
    notification_service = ContestNotificationService(session, bot)
    success, failed = await notification_service.notify_contest_ended(contest)
    await callback.message.answer(
        f"📣 Konkurs yakuni haqida ishtirokchilarga xabar yuborildi.\n"
        f"📤 Yuborildi: {success}\n❌ Xato: {failed}"
    )


# ---------- Vaqtni o'zgartirish ----------

@router.callback_query(lambda c: c.data == "sa:reschedule")
async def reschedule_start(callback: CallbackQuery, state: FSMContext, session: AsyncSession) -> None:
    from app.repositories.contest_repo import ContestRepository

    contest_repo = ContestRepository(session)
    contest = await contest_repo.get_scheduled_or_active()

    if not contest:
        await callback.answer("Faol konkurs topilmadi.", show_alert=True)
        return

    await state.update_data(contest_id=contest.id)
    await state.set_state(RescheduleContestStates.new_value)
    await callback.message.edit_text(
        f"🕒 Joriy vaqtlar:\nBoshlanish: {format_dt(contest.start_at)}\nTugash: {format_dt(contest.end_at)}\n\n"
        f"Yangi qiymatlarni <code>start|end</code> formatida kiriting:\n"
        f"Masalan: <code>2026-08-16 10:00|2026-08-22 20:00</code>",
        reply_markup=back_to_sa_kb(),
    )
    await callback.answer()


@router.message(RescheduleContestStates.new_value)
async def reschedule_apply(message: Message, state: FSMContext, session: AsyncSession) -> None:
    data = await state.get_data()
    await state.clear()

    try:
        start_str, end_str = message.text.strip().split("|")
        start_at = dt.datetime.strptime(start_str.strip(), DATETIME_FORMAT).replace(tzinfo=dt.timezone.utc)
        end_at = dt.datetime.strptime(end_str.strip(), DATETIME_FORMAT).replace(tzinfo=dt.timezone.utc)
    except (ValueError, IndexError):
        await message.answer("❌ Format xato. Masalan: <code>2026-08-16 10:00|2026-08-22 20:00</code>")
        return

    contest_service = ContestService(session)
    await contest_service.reschedule(data["contest_id"], start_at, end_at)
    await message.answer("✅ Konkurs vaqti yangilandi.", reply_markup=superadmin_panel_kb())


# ---------- Arxiv ----------

@router.callback_query(lambda c: c.data == "sa:archive")
async def show_archive(callback: CallbackQuery, session: AsyncSession) -> None:
    contest_service = ContestService(session)
    contests = await contest_service.list_archive(limit=20)

    if not contests:
        await callback.message.edit_text("🗂 Arxiv bo'sh.", reply_markup=back_to_sa_kb())
        await callback.answer()
        return

    lines = ["🗂 <b>Arxiv konkurslar</b>\n"]
    for c in contests:
        lines.append(
            f"• {c.title} — {contest_status_uz(c.status.value)}\n"
            f"  {format_dt(c.start_at)} → {format_dt(c.end_at)}"
        )
    await callback.message.edit_text("\n".join(lines), reply_markup=back_to_sa_kb())
    await callback.answer()
