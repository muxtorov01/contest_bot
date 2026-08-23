"""Asosiy menyu: referral havola, statistika, TOP 20, shartlar."""
from __future__ import annotations

from aiogram import Router, F, Bot
from aiogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.keyboards.user_kb import referral_link_kb
from app.services.contest_service import ContestService
from app.services.rating_service import RatingService
from app.services.referral_service import ReferralService
from app.utils.text import format_dt

router = Router(name="user_menu")


@router.message(F.text == "🔗 Referral havolam")
async def my_referral_link(message: Message, session: AsyncSession) -> None:
    user_id = message.from_user.id
    link = f"https://t.me/{settings.BOT_USERNAME}?start={user_id}"

    contest_service = ContestService(session)
    contest = await contest_service.get_current_for_user()

    lines = [
        "🔗 <b>Sizning shaxsiy referral havolangiz:</b>",
        "",
        f"<code>{link}</code>",
        "",
    ]
    if contest:
        lines.append(f"🏁 Joriy konkurs: <b>{contest.title}</b>")
        lines.append(f"{contest.description}")
        lines.append("")
    lines.append(
        "Do'stlaringizni shu havola orqali taklif qiling. Ular captcha va kanallarga "
        "obuna bo'lgandan so'ng, sizga ball qo'shiladi!"
    )

    await message.answer(
        "\n".join(lines),
        reply_markup=referral_link_kb(user_id, contest),
    )


@router.message(F.text == "📊 Statistikam")
async def my_stats(message: Message, session: AsyncSession, bot: Bot) -> None:
    contest_service = ContestService(session)
    contest = await contest_service.get_current_for_user()

    if not contest:
        await message.answer("ℹ️ Hozircha aktiv konkurs mavjud emas.")
        return

    referral_service = ReferralService(session, bot)
    rating_service = RatingService(session)

    count = await referral_service.get_user_verified_count(contest.id, message.from_user.id)
    rank, _ = await rating_service.get_user_rank(contest.id, message.from_user.id)

    rank_text = f"#{rank}" if rank else "reytingda emassiz"

    await message.answer(
        f"📊 <b>Sizning statistikangiz</b>\n\n"
        f"🎯 Verified referral: <b>{count}</b>\n"
        f"📍 O'rningiz: <b>{rank_text}</b>\n"
        f"🏁 Konkurs: {contest.title}\n"
        f"⏰ Tugash vaqti: {format_dt(contest.end_at)}"
    )


@router.message(F.text == "🏆 TOP 20")
async def top20(message: Message, session: AsyncSession) -> None:
    contest_service = ContestService(session)
    contest = await contest_service.get_current_for_user()

    if not contest:
        await message.answer("ℹ️ Hozircha aktiv konkurs mavjud emas.")
        return

    rating_service = RatingService(session)
    top_list = await rating_service.get_top(contest.id, limit=20)
    rank, count = await rating_service.get_user_rank(contest.id, message.from_user.id)

    text = rating_service.format_top_message(top_list, rank, count)
    await message.answer(text)


@router.message(F.text == "📜 Shartlar")
async def rules(message: Message, session: AsyncSession) -> None:
    contest_service = ContestService(session)
    contest = await contest_service.get_current_for_user()

    if not contest:
        await message.answer("ℹ️ Hozircha aktiv konkurs mavjud emas.")
        return

    text = (
        f"📜 <b>{contest.title}</b>\n\n"
        f"{contest.description}\n\n"
        f"⏰ Boshlanish: {format_dt(contest.start_at)}\n"
        f"⏰ Tugash: {format_dt(contest.end_at)}\n\n"
        "📌 <b>Qatnashish shartlari:</b>\n"
        "1️⃣ Barcha majburiy kanallarga obuna bo'ling\n"
        "2️⃣ Shaxsiy referral havolangiz orqali do'stlaringizni taklif qiling\n"
        "3️⃣ Har bir tasdiqlangan (VERIFIED) taklif uchun 1 ball olasiz\n"
        "4️⃣ Kanaldan chiqib ketsangiz, ball bekor qilinadi\n"
        "5️⃣ Konkurs oxirida eng ko'p ball to'plagan foydalanuvchilar g'olib bo'ladi"
    )
    await message.answer(text)
