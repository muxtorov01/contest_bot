"""Admin panel klaviaturasi."""
from __future__ import annotations

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def admin_panel_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🏆 TOP 50", callback_data="admin:top50")],
            [InlineKeyboardButton(text="🔍 User qidirish", callback_data="admin:search")],
            [InlineKeyboardButton(text="📥 Excel eksport", callback_data="admin:export")],
        ]
    )


def back_to_admin_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text="⬅️ Orqaga", callback_data="admin:panel")]]
    )
