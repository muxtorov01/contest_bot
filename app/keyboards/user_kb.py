"""User uchun klaviaturalar."""
from __future__ import annotations

from urllib.parse import quote

from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    ReplyKeyboardMarkup,
    KeyboardButton,
)

from app.config import settings


def main_menu_kb() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🔗 Referral havolam"), KeyboardButton(text="📊 Statistikam")],
            [KeyboardButton(text="🏆 TOP 20"), KeyboardButton(text="📜 Shartlar")],
        ],
        resize_keyboard=True,
    )


def referral_link_kb(user_id: int, contest=None) -> InlineKeyboardMarkup:
    """Referral havolasini ulashish tugmasi.
    Agar joriy konkurs berilsa, ulashiladigan matn konkurs nomi va tavsifi bilan boradi,
    shunda havolani ochgan odam qaysi konkurs bo'layotganini darhol ko'radi."""
    link = f"https://t.me/{settings.BOT_USERNAME}?start={user_id}"

    if contest:
        share_text = (
            f"🎁 {contest.title} nomli konkursga qo'shiling!\n\n{contest.description}"
        )
    else:
        share_text = "Konkursga qo'shiling va sovg'a yutib oling! 🎁"

    share_url = f"https://t.me/share/url?url={quote(link, safe='')}&text={quote(share_text, safe='')}"
    return InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text="📤 Ulashish", url=share_url)]]
    )


def subscribe_channels_kb(channels: list, check_callback: str = "check_subscription") -> InlineKeyboardMarkup:
    buttons = []
    for channel in channels:
        url = channel.invite_link or (
            f"https://t.me/{channel.username}" if channel.username else None
        )
        if url:
            buttons.append([InlineKeyboardButton(text=f"➕ {channel.title}", url=url)])
    buttons.append([InlineKeyboardButton(text="✅ Tekshirish", callback_data=check_callback)])
    return InlineKeyboardMarkup(inline_keyboard=buttons)
