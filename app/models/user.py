"""Foydalanuvchi modeli."""
from __future__ import annotations

import datetime as dt

from sqlalchemy import BigInteger, String, DateTime, func, Boolean
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=False)  # telegram_id
    username: Mapped[str | None] = mapped_column(String(64), nullable=True)
    full_name: Mapped[str | None] = mapped_column(String(255), nullable=True)

    is_blocked: Mapped[bool] = mapped_column(Boolean, default=False)
    is_captcha_verified: Mapped[bool] = mapped_column(Boolean, default=False)

    captcha_fail_count: Mapped[int] = mapped_column(default=0)
    captcha_blocked_until: Mapped[dt.datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    created_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[dt.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    def __repr__(self) -> str:
        return f"<User {self.id} @{self.username}>"
