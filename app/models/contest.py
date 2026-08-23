"""Konkurs modeli."""
from __future__ import annotations

import datetime as dt
import enum

from sqlalchemy import String, Text, DateTime, Enum, func, BigInteger
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class ContestStatus(str, enum.Enum):
    SCHEDULED = "scheduled"
    ACTIVE = "active"
    ENDED = "ended"
    STOPPED = "stopped"


class Contest(Base):
    __tablename__ = "contests"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(255))
    description: Mapped[str] = mapped_column(Text, default="")

    start_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True))
    end_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True))

    status: Mapped[ContestStatus] = mapped_column(
        Enum(
            ContestStatus,
            name="contest_status",
            values_callable=lambda enum_cls: [member.value for member in enum_cls],
        ),
        default=ContestStatus.SCHEDULED,
    )

    created_by: Mapped[int] = mapped_column(BigInteger)
    created_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[dt.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    def __repr__(self) -> str:
        return f"<Contest {self.id} {self.title} [{self.status}]>"
