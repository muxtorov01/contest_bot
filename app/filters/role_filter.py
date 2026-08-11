"""Handlerlarni rol bo'yicha cheklovchi filter."""
from __future__ import annotations

from typing import Any

from aiogram.filters import BaseFilter
from aiogram.types import TelegramObject

ROLE_HIERARCHY = {"user": 0, "admin": 1, "superadmin": 2}


class RoleFilter(BaseFilter):
    """Masalan: RoleFilter("admin") -> admin va superadmin uchun ruxsat beradi."""

    def __init__(self, min_role: str) -> None:
        self.min_role = min_role

    async def __call__(self, event: TelegramObject, role: str, **kwargs: Any) -> bool:
        return ROLE_HIERARCHY.get(role, 0) >= ROLE_HIERARCHY.get(self.min_role, 0)
