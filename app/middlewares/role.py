"""Foydalanuvchi rolini aniqlab, handlerlarga `data["role"]` orqali uzatadi.
Rol: 'user' | 'admin' | 'superadmin'."""
from __future__ import annotations

from typing import Any, Awaitable, Callable, Dict

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models.admin import AdminRole
from app.repositories.admin_repo import AdminRepository


class RoleMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        user = data.get("event_from_user")
        role = "user"

        if user:
            if user.id in settings.superadmin_ids:
                role = "superadmin"
            else:
                session: AsyncSession = data["session"]
                admin_repo = AdminRepository(session)
                admin = await admin_repo.get(user.id)
                if admin:
                    role = "superadmin" if admin.role == AdminRole.SUPERADMIN else "admin"

        data["role"] = role
        return await handler(event, data)
