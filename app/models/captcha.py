"""Captcha urinishlari tarixi (ixtiyoriy log jadvali)."""
from __future__ import annotations

import datetime as dt

from sqlalchemy import BigInteger, DateTime, Boolean, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class CaptchaAttempt(Base):
    __tablename__ = "captcha_attempts"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(BigInteger)
    success: Mapped[bool] = mapped_column(Boolean)
    created_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
