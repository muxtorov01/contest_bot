"""Excel eksport bilan bog'liq logika."""
from __future__ import annotations

import io

from openpyxl import Workbook
from openpyxl.styles import Font
from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.referral_repo import ReferralRepository
from app.repositories.user_repo import UserRepository


class ExportService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.referral_repo = ReferralRepository(session)
        self.user_repo = UserRepository(session)

    async def export_leaderboard_to_excel(self, contest_id: int, contest_title: str) -> io.BytesIO:
        ranking = await self.referral_repo.full_ranking(contest_id)

        wb = Workbook()
        ws = wb.active
        ws.title = "Reyting"

        headers = ["O'rin", "Telegram ID", "Username", "F.I.O", "Verified referral"]
        ws.append(headers)
        for cell in ws[1]:
            cell.font = Font(bold=True)

        for rank, (user_id, count) in enumerate(ranking, start=1):
            user = await self.user_repo.get(user_id)
            username = f"@{user.username}" if user and user.username else "-"
            full_name = user.full_name if user and user.full_name else "-"
            ws.append([rank, user_id, username, full_name, count])

        for column_cells in ws.columns:
            length = max(len(str(cell.value)) for cell in column_cells)
            ws.column_dimensions[column_cells[0].column_letter].width = length + 4

        buffer = io.BytesIO()
        wb.save(buffer)
        buffer.seek(0)
        return buffer
