"""
Loyihaning markaziy konfiguratsiya moduli.
Barcha sozlamalar .env fayldan pydantic-settings orqali o'qiladi.
"""
from __future__ import annotations

from typing import List

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # --- Bot ---
    BOT_TOKEN: str
    BOT_USERNAME: str

    # --- Superadminlar ---
    SUPERADMIN_IDS: str = ""

    # --- Webhook ---
    USE_WEBHOOK: bool = True
    WEBHOOK_HOST: str = ""
    WEBHOOK_PATH: str = "/webhook"
    WEBAPP_HOST: str = "0.0.0.0"
    WEBAPP_PORT: int = 8080

    # --- Database ---
    DATABASE_URL: str
    SYNC_DATABASE_URL: str = ""

    # --- Backup ---
    BACKUP_CHANNEL_ID: int = 0
    BACKUP_INTERVAL_HOURS: int = 24

    # --- Boshqa ---
    LOG_LEVEL: str = "INFO"
    TIMEZONE: str = "Asia/Tashkent"
    CAPTCHA_MAX_ATTEMPTS: int = 3
    CAPTCHA_BLOCK_SECONDS: int = 30
    SUBSCRIPTION_RECHECK_INTERVAL_HOURS: int = 1

    @property
    def superadmin_ids(self) -> List[int]:
        if not self.SUPERADMIN_IDS:
            return []
        return [int(x.strip()) for x in self.SUPERADMIN_IDS.split(",") if x.strip()]

    @property
    def webhook_url(self) -> str:
        return f"{self.WEBHOOK_HOST.rstrip('/')}{self.WEBHOOK_PATH}"


settings = Settings()
