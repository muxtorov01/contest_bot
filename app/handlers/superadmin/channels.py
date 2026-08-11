"""Superadmin: majburiy kanallarni boshqarish."""
from __future__ import annotations

from aiogram import Router, Bot
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession

from app.filters.role_filter import RoleFilter
from app.keyboards.superadmin_kb import channels_management_kb, back_to_sa_kb
from app.repositories.channel_repo import ChannelRepository
from app.repositories.contest_repo import ContestRepository
from app.services.subscription_service import SubscriptionService
from app.states.contest_states import AddChannelStates

router = Router(name="superadmin_channels")
router.message.filter(RoleFilter("superadmin"))
router.callback_query.filter(RoleFilter("superadmin"))


@router.callback_query(lambda c: c.data == "sa:channels")
async def list_channels(callback: CallbackQuery, session: AsyncSession) -> None:
    contest_repo = ContestRepository(session)
    contest = await contest_repo.get_scheduled_or_active()

    if not contest:
        await callback.answer("Avval konkurs yarating.", show_alert=True)
        return

    channel_repo = ChannelRepository(session)
    channels = await channel_repo.list_active_for_contest(contest.id)

    text = "📡 <b>Majburiy kanallar</b>\n\n" + (
        "\n".join(f"• {ch.title}" for ch in channels) if channels else "Hozircha kanal biriktirilmagan."
    )
    await callback.message.edit_text(text, reply_markup=channels_management_kb(channels))
    await callback.answer()


@router.callback_query(lambda c: c.data == "sa:add_channel")
async def add_channel_start(callback: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(AddChannelStates.waiting_channel)
    await callback.message.edit_text(
        "📡 Kanal username'ini (@kanal) yoki chat_id'sini yuboring.\n\n"
        "⚠️ Bot avval shu kanalda <b>admin</b> qilib qo'yilgan bo'lishi shart!",
        reply_markup=back_to_sa_kb(),
    )
    await callback.answer()


@router.message(AddChannelStates.waiting_channel)
async def add_channel_process(message: Message, state: FSMContext, session: AsyncSession, bot: Bot) -> None:
    await state.clear()
    raw = message.text.strip()

    try:
        chat = await bot.get_chat(raw if raw.startswith("@") else int(raw))
    except Exception as e:
        await message.answer(f"❌ Kanal topilmadi yoki noto'g'ri format: {e}")
        return

    contest_repo = ContestRepository(session)
    contest = await contest_repo.get_scheduled_or_active()
    if not contest:
        await message.answer("❌ Avval konkurs yarating.")
        return

    channel_repo = ChannelRepository(session)
    channel = await channel_repo.add(
        contest_id=contest.id,
        chat_id=chat.id,
        title=chat.title or chat.username or str(chat.id),
        username=chat.username,
        invite_link=chat.invite_link,
    )

    subscription_service = SubscriptionService(session, bot)
    is_admin = await subscription_service.verify_bot_is_admin(channel)

    warn = "" if is_admin else "\n\n⚠️ <b>Diqqat:</b> bot bu kanalda hali admin emas!"
    await message.answer(f"✅ Kanal biriktirildi: <b>{channel.title}</b>{warn}")


@router.callback_query(lambda c: c.data.startswith("sa:remove_channel:"))
async def remove_channel(callback: CallbackQuery, session: AsyncSession) -> None:
    channel_id = int(callback.data.split(":")[-1])
    channel_repo = ChannelRepository(session)
    await channel_repo.remove(channel_id)
    await callback.answer("✅ Kanal o'chirildi")
    await list_channels(callback, session)
