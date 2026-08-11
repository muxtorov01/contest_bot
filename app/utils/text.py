"""Umumiy matn shablon va yordamchi funksiyalar."""
from __future__ import annotations

import datetime as dt


def format_dt(value: dt.datetime | None) -> str:
    if not value:
        return "—"
    return value.strftime("%Y-%m-%d %H:%M")


def contest_status_uz(status: str) -> str:
    mapping = {
        "scheduled": "⏳ Rejalashtirilgan",
        "active": "🟢 Aktiv",
        "ended": "🔴 Tugagan",
        "stopped": "⛔️ To'xtatilgan",
    }
    return mapping.get(status, status)
