"""Oddiy throttling middleware — spam bosishlardan himoya."""
from __future__ import annotations

import time
from typing import Any, Awaitable, Callable, Dict

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject

THROTTLE_SECONDS = 0.6


class ThrottlingMiddleware(BaseMiddleware):
    def __init__(self) -> None:
        self._last_call: dict[int, float] = {}

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        user = data.get("event_from_user")
        if user:
            now = time.monotonic()
            last = self._last_call.get(user.id, 0)
            if now - last < THROTTLE_SECONDS:
                return None
            self._last_call[user.id] = now
        return await handler(event, data)
