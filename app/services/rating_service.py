"""Top ro'yxat va reyting bilan bog'liq logika."""
from __future__ import annotations

from html import escape

from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.referral_repo import ReferralRepository
from app.repositories.user_repo import UserRepository

MEDALS = {1: "🥇", 2: "🥈", 3: "🥉"}


class RatingService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.referral_repo = ReferralRepository(session)
        self.user_repo = UserRepository(session)

    async def get_top(self, contest_id: int, limit: int = 20) -> list[dict]:
        leaderboard = await self.referral_repo.leaderboard(contest_id, limit)
        result = []
        for rank, (referrer_id, count) in enumerate(leaderboard, start=1):
            user = await self.user_repo.get(referrer_id)
            name = self._display_name(user, referrer_id)
            result.append({"rank": rank, "user_id": referrer_id, "name": name, "count": count})
        return result

    async def get_top_50(self, contest_id: int) -> list[dict]:
        return await self.get_top(contest_id, limit=50)

    async def get_user_rank(self, contest_id: int, user_id: int) -> tuple[int | None, int]:
        """(o'rin, ball) qaytaradi. Agar referral yo'q bo'lsa o'rin=None, ball=0."""
        full_ranking = await self.referral_repo.full_ranking(contest_id)
        count = await self.referral_repo.count_verified(contest_id, user_id)
        for rank, (referrer_id, _cnt) in enumerate(full_ranking, start=1):
            if referrer_id == user_id:
                return rank, count
        return None, count

    @staticmethod
    def format_top_message(top_list: list[dict], user_rank: int | None, user_count: int) -> str:
        lines = ["🏆 <b>TOP 20</b>\n"]
        if not top_list:
            lines.append("Hozircha hech kim ball to'plamagan.")
        for entry in top_list:
            prefix = MEDALS.get(entry["rank"], f"{entry['rank']}.")
            lines.append(f"{prefix} {entry['name']} — {entry['count']}")

        lines.append("")
        if user_rank:
            lines.append(f"📍 Sizning o'rningiz: #{user_rank}")
        else:
            lines.append("📍 Sizning o'rningiz: hali reytingda emassiz")
        lines.append(f"🎯 Verified referral: {user_count}")
        return "\n".join(lines)

    @staticmethod
    def _display_name(user, fallback_id: int) -> str:
        if not user:
            return f"ID{fallback_id}"
        if user.username:
            return escape(f"@{user.username}")
        return escape(user.full_name) if user.full_name else f"ID{fallback_id}"
