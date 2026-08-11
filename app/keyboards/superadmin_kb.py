"""Superadmin panel klaviaturalari."""
from __future__ import annotations

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def superadmin_panel_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🆕 Konkurs yaratish", callback_data="sa:create_contest")],
            [
                InlineKeyboardButton(text="▶️ Boshlash", callback_data="sa:start_now"),
                InlineKeyboardButton(text="⏹ Tugatish", callback_data="sa:stop_now"),
            ],
            [InlineKeyboardButton(text="🕒 Vaqtni o'zgartirish", callback_data="sa:reschedule")],
            [InlineKeyboardButton(text="📡 Majburiy kanallar", callback_data="sa:channels")],
            [InlineKeyboardButton(text="👮 Adminlar", callback_data="sa:admins")],
            [InlineKeyboardButton(text="📢 Broadcast", callback_data="sa:broadcast")],
            [InlineKeyboardButton(text="🗄 Backup yaratish", callback_data="sa:backup")],
            [InlineKeyboardButton(text="🗂 Arxiv konkurslar", callback_data="sa:archive")],
        ]
    )


def confirm_kb(yes_cb: str, no_cb: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ Ha", callback_data=yes_cb),
                InlineKeyboardButton(text="❌ Yo'q", callback_data=no_cb),
            ]
        ]
    )


def back_to_sa_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text="⬅️ Orqaga", callback_data="sa:panel")]]
    )


def channels_management_kb(channels: list) -> InlineKeyboardMarkup:
    buttons = [
        [InlineKeyboardButton(text=f"❌ {ch.title}", callback_data=f"sa:remove_channel:{ch.id}")]
        for ch in channels
    ]
    buttons.append([InlineKeyboardButton(text="➕ Kanal qo'shish", callback_data="sa:add_channel")])
    buttons.append([InlineKeyboardButton(text="⬅️ Orqaga", callback_data="sa:panel")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def admins_management_kb(admins: list) -> InlineKeyboardMarkup:
    buttons = [
        [InlineKeyboardButton(text=f"❌ {a.id} ({a.role.value})", callback_data=f"sa:remove_admin:{a.id}")]
        for a in admins
    ]
    buttons.append([InlineKeyboardButton(text="➕ Admin qo'shish", callback_data="sa:add_admin")])
    buttons.append([InlineKeyboardButton(text="⬅️ Orqaga", callback_data="sa:panel")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)
