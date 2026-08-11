"""User bilan bog'liq DB operatsiyalari."""
from __future__ import annotations

import datetime as dt

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User


class UserRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get(self, user_id: int) -> User | None:
        return await self.session.get(User, user_id)

    async def get_or_create(self, user_id: int, username: str | None, full_name: str | None) -> tuple[User, bool]:
        user = await self.get(user_id)
        if user:
            # profil ma'lumotlarini yangilab qo'yamiz
            user.username = username
            user.full_name = full_name
            return user, False
        user = User(id=user_id, username=username, full_name=full_name)
        self.session.add(user)
        await self.session.flush()
        return user, True

    async def set_captcha_verified(self, user_id: int, value: bool = True) -> None:
        user = await self.get(user_id)
        if user:
            user.is_captcha_verified = value
            user.captcha_fail_count = 0
            user.captcha_blocked_until = None

    async def register_captcha_fail(self, user_id: int, max_attempts: int, block_seconds: int) -> int:
        user = await self.get(user_id)
        if not user:
            return 0
        user.captcha_fail_count += 1
        if user.captcha_fail_count >= max_attempts:
            user.captcha_blocked_until = dt.datetime.now(dt.timezone.utc) + dt.timedelta(seconds=block_seconds)
            user.captcha_fail_count = 0
        return user.captcha_fail_count

    async def is_captcha_blocked(self, user_id: int) -> bool:
        user = await self.get(user_id)
        if not user or not user.captcha_blocked_until:
            return False
        return user.captcha_blocked_until > dt.datetime.now(dt.timezone.utc)

    async def search(self, query: str, limit: int = 20) -> list[User]:
        """ID, username yoki ism bo'yicha qidiruv."""
        stmt = select(User).limit(limit)
        if query.isdigit():
            stmt = select(User).where(User.id == int(query))
        else:
            like = f"%{query.lstrip('@')}%"
            stmt = select(User).where(
                (User.username.ilike(like)) | (User.full_name.ilike(like))
            ).limit(limit)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def count_all(self) -> int:
        result = await self.session.execute(select(func.count(User.id)))
        return result.scalar_one()

    async def set_blocked(self, user_id: int, blocked: bool = True) -> None:
        user = await self.get(user_id)
        if user:
            user.is_blocked = blocked

    async def all_active_ids(self) -> list[int]:
        result = await self.session.execute(select(User.id).where(User.is_blocked.is_(False)))
        return [row[0] for row in result.all()]
