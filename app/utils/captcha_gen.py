"""Oddiy inline tugmali captcha generatori (matematik amal)."""
from __future__ import annotations

import random

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def generate_captcha() -> tuple[str, int, InlineKeyboardMarkup]:
    """Qaytaradi: (savol matni, to'g'ri javob, inline klaviatura)."""
    a, b = random.randint(1, 9), random.randint(1, 9)
    correct = a + b
    question = f"🔐 Botga inson ekanligingizni tasdiqlang:\n\n<b>{a} + {b} = ?</b>"

    options = {correct}
    while len(options) < 4:
        options.add(random.randint(2, 18))
    options_list = list(options)
    random.shuffle(options_list)

    buttons = [
        InlineKeyboardButton(text=str(opt), callback_data=f"captcha:{opt}:{correct}")
        for opt in options_list
    ]
    keyboard = InlineKeyboardMarkup(inline_keyboard=[buttons[:2], buttons[2:]])
    return question, correct, keyboard
