"""Admin/Superadmin modeli."""
from __future__ import annotations

import datetime as dt
import enum

from sqlalchemy import BigInteger, DateTime, Enum, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class AdminRole(str, enum.Enum):
    ADMIN = "admin"
    SUPERADMIN = "superadmin"


class Admin(Base):
    __tablename__ = "admins"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=False)
    role: Mapped[AdminRole] = mapped_column(Enum(AdminRole, name="admin_role"), default=AdminRole.ADMIN)
    added_by: Mapped[int] = mapped_column(BigInteger)
    created_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    def __repr__(self) -> str:
        return f"<Admin {self.id} [{self.role}]>"
