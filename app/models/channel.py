"""Majburiy obuna kanallari modeli."""
from __future__ import annotations

import datetime as dt

from sqlalchemy import BigInteger, String, DateTime, ForeignKey, func, Boolean
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class RequiredChannel(Base):
    __tablename__ = "required_channels"

    id: Mapped[int] = mapped_column(primary_key=True)
    contest_id: Mapped[int] = mapped_column(ForeignKey("contests.id", ondelete="CASCADE"))

    chat_id: Mapped[int] = mapped_column(BigInteger)
    username: Mapped[str | None] = mapped_column(String(64), nullable=True)
    title: Mapped[str] = mapped_column(String(255))
    invite_link: Mapped[str | None] = mapped_column(String(255), nullable=True)

    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    def __repr__(self) -> str:
        return f"<RequiredChannel {self.chat_id} {self.title}>"
