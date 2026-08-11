"""PostgreSQL backup yaratish va Telegram kanaliga yuborish logikasi."""
from __future__ import annotations

import asyncio
import datetime as dt
import os
import subprocess

from aiogram import Bot
from aiogram.types import BufferedInputFile

from app.config import settings
from app.utils.logger import logger


class BackupService:
    def __init__(self, bot: Bot) -> None:
        self.bot = bot

    async def create_and_send_backup(self) -> bool:
        """pg_dump orqali backup yaratadi va sozlangan yopiq kanalga yuboradi."""
        try:
            dump_path = await self._create_dump()
        except Exception as e:
            logger.error(f"Backup yaratishda xato: {e}")
            return False

        try:
            with open(dump_path, "rb") as f:
                data = f.read()
            filename = os.path.basename(dump_path)
            caption = (
                f"🗄 Avtomatik backup\n"
                f"📅 {dt.datetime.now(dt.timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}"
            )
            if settings.BACKUP_CHANNEL_ID:
                await self.bot.send_document(
                    chat_id=settings.BACKUP_CHANNEL_ID,
                    document=BufferedInputFile(data, filename=filename),
                    caption=caption,
                )
            logger.info("Backup muvaffaqiyatli yuborildi")
            return True
        except Exception as e:
            logger.error(f"Backupni yuborishda xato: {e}")
            return False
        finally:
            if os.path.exists(dump_path):
                os.remove(dump_path)

    async def _create_dump(self) -> str:
        """pg_dump ni subprocess orqali async ravishda chaqiradi."""
        timestamp = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%d_%H%M%S")
        dump_path = f"/tmp/backup_{timestamp}.sql"

        # SYNC_DATABASE_URL psycopg formatida bo'lishi kerak (pg_dump uchun)
        db_url = settings.SYNC_DATABASE_URL or settings.DATABASE_URL.replace(
            "postgresql+asyncpg://", "postgresql://"
        )

        cmd = ["pg_dump", db_url, "-f", dump_path, "--no-owner", "--no-privileges"]

        proc = await asyncio.create_subprocess_exec(
            *cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )
        _, stderr = await proc.communicate()

        if proc.returncode != 0:
            raise RuntimeError(f"pg_dump xatosi: {stderr.decode(errors='ignore')}")

        return dump_path
