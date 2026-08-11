"""
Async SQLAlchemy engine, session factory va Base.
MUHIM: bu yerda hech qanday Base.metadata.drop_all() chaqirilmaydi.
Ma'lumotlar faqat PostgreSQL'da, doimiy saqlanadi.
"""
from __future__ import annotations

from contextlib import asynccontextmanager
from typing import AsyncIterator

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

from app.config import settings


class Base(DeclarativeBase):
    """Barcha modellar uchun umumiy asos."""
    pass


engine = create_async_engine(
    settings.DATABASE_URL,
    echo=False,
    pool_pre_ping=True,   # Railway'da uyquga ketgan connectionlarni tekshiradi
    pool_size=10,
    max_overflow=20,
)

async_session_factory = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)


@asynccontextmanager
async def get_session() -> AsyncIterator[AsyncSession]:
    """Har bir so'rov uchun alohida sessiya yaratadi va yopadi."""
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
