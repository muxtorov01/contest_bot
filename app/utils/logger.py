"""Loguru asosidagi markazlashgan logger."""
from __future__ import annotations

import sys

from loguru import logger

from app.config import settings

logger.remove()
logger.add(
    sys.stdout,
    level=settings.LOG_LEVEL,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | "
    "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
)
logger.add(
    "logs/bot.log",
    level="INFO",
    rotation="10 MB",
    retention="14 days",
    compression="zip",
)

__all__ = ["logger"]
