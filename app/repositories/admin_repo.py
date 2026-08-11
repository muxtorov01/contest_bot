"""Admin/Superadmin bilan bog'liq DB operatsiyalari."""
from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.admin import Admin, AdminRole


class AdminRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get(self, user_id: int) -> Admin | None:
        return await self.session.get(Admin, user_id)

    async def list_all(self) -> list[Admin]:
        result = await self.session.execute(select(Admin))
        return list(result.scalars().all())

    async def add(self, user_id: int, role: AdminRole, added_by: int) -> Admin:
        existing = await self.get(user_id)
        if existing:
            existing.role = role
            return existing
        admin = Admin(id=user_id, role=role, added_by=added_by)
        self.session.add(admin)
        await self.session.flush()
        return admin

    async def remove(self, user_id: int) -> bool:
        admin = await self.get(user_id)
        if admin:
            await self.session.delete(admin)
            return True
        return False
