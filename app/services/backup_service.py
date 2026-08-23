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

    async def create_and_send_backup(self, chat_id: int | None = None) -> bool:
        """pg_dump orqali backup yaratadi va sozlangan yopiq kanalga (va/yoki berilgan chat_id'ga) yuboradi.

        MUHIM (tuzatilgan xato): avval BACKUP_CHANNEL_ID sozlanmagan bo'lsa,
        funksiya hech kimga hech narsa yubormay turib ham True (muvaffaqiyat) qaytarardi.
        Endi kamida bitta manzilga (kanal yoki chat_id) yuborilmasa, False qaytaradi
        va aniq xato logga yoziladi."""
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
                f"🗄 Backup\n"
                f"📅 {dt.datetime.now(dt.timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}"
            )

            targets: list[int] = []
            if settings.BACKUP_CHANNEL_ID:
                targets.append(settings.BACKUP_CHANNEL_ID)
            if chat_id and chat_id not in targets:
                targets.append(chat_id)

            if not targets:
                logger.error(
                    "Backup yuborilmadi: BACKUP_CHANNEL_ID sozlanmagan va chat_id berilmagan."
                )
                return False

            for target in targets:
                await self.bot.send_document(
                    chat_id=target,
                    document=BufferedInputFile(data, filename=filename),
                    caption=caption,
                )

            logger.info(f"Backup muvaffaqiyatli yuborildi: {targets}")
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
