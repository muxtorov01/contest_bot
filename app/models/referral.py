"""Referral (taklif) modeli."""
from __future__ import annotations

import datetime as dt
import enum

from sqlalchemy import BigInteger, DateTime, Enum, ForeignKey, func, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class ReferralStatus(str, enum.Enum):
    PENDING = "pending"
    VERIFIED = "verified"
    CANCELLED = "cancelled"


class Referral(Base):
    __tablename__ = "referrals"
    __table_args__ = (
        UniqueConstraint("invited_id", name="uq_referral_invited_once"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    contest_id: Mapped[int] = mapped_column(ForeignKey("contests.id", ondelete="CASCADE"))

    referrer_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id", ondelete="CASCADE"))
    invited_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id", ondelete="CASCADE"))

    status: Mapped[ReferralStatus] = mapped_column(
        Enum(ReferralStatus, name="referral_status"), default=ReferralStatus.PENDING
    )

    created_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    verified_at: Mapped[dt.datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    cancelled_at: Mapped[dt.datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    def __repr__(self) -> str:
        return f"<Referral {self.referrer_id}->{self.invited_id} [{self.status}]>"
