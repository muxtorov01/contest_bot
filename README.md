# 🏆 Telegram Konkurs / Referral Bot

Production-level Telegram konkurs va referral tizimi boti.
**Texnologiyalar:** Python 3.12, aiogram 3.x, PostgreSQL, SQLAlchemy (async), Alembic, APScheduler, Railway (webhook).

Barcha xabarlar, tugmalar va admin panel **to'liq o'zbekcha**.

---

## 📁 Loyiha strukturasi

```
contest_bot/
├── app/
│   ├── main.py                  # Kirish nuqtasi (webhook server)
│   ├── config.py                # .env dan sozlamalarni o'qiydi
│   ├── database.py               # Async engine, session factory, Base
│   ├── models/                  # SQLAlchemy modellari
│   │   ├── user.py
│   │   ├── contest.py
│   │   ├── channel.py
│   │   ├── referral.py
│   │   ├── admin.py
│   │   └── captcha.py
│   ├── repositories/            # Repository pattern — faqat DB so'rovlari
│   │   ├── user_repo.py
│   │   ├── contest_repo.py
│   │   ├── channel_repo.py
│   │   ├── referral_repo.py
│   │   └── admin_repo.py
│   ├── services/                # Biznes logika
│   │   ├── contest_service.py
│   │   ├── subscription_service.py
│   │   ├── referral_service.py
│   │   ├── rating_service.py
│   │   ├── export_service.py
│   │   ├── broadcast_service.py
│   │   └── backup_service.py
│   ├── handlers/
│   │   ├── user/                 # start, captcha, menu (referral link, stats, top20, rules)
│   │   ├── admin/                 # panel (top50), search, export
│   │   └── superadmin/            # contest, channels, admins, broadcast, backup
│   ├── middlewares/
│   │   ├── db_session.py         # har update uchun DB session
│   │   ├── role.py                # user/admin/superadmin aniqlash
│   │   └── throttling.py
│   ├── filters/
│   │   └── role_filter.py        # RoleFilter("admin") kabi handler cheklovlari
│   ├── states/                   # FSM holatlari
│   ├── keyboards/                # Inline/Reply klaviaturalar
│   ├── scheduler/
│   │   └── jobs.py                # APScheduler: auto start/end, recheck, backup
│   └── utils/
│       ├── logger.py
│       ├── captcha_gen.py
│       └── text.py
├── alembic/                      # Migratsiyalar (ma'lumotni saqlagan holda ishlaydi)
├── requirements.txt
├── .env.example
├── alembic.ini
├── Procfile                       # Railway: release + web
├── railway.json
├── nixpacks.toml
└── README.md
```

---

## ⚙️ O'rnatish (lokal)

```bash
git clone <repo>
cd contest_bot
python3.12 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

cp .env.example .env
# .env faylni to'ldiring: BOT_TOKEN, BOT_USERNAME, SUPERADMIN_IDS, DATABASE_URL ...

# Migratsiyalarni ishga tushirish
alembic upgrade head

# Botni ishga tushirish (polling uchun .env da USE_WEBHOOK=false qiling)
python -m app.main
```

---

## 🚂 Railway'ga deploy qilish

### 1. Ikkita alohida service yarating

**a) PostgreSQL service**
Railway dashboard → *New* → *Database* → *Add PostgreSQL*.
Railway avtomatik `DATABASE_URL` beradi (`postgresql://...` formatida).

> ⚠️ SQLAlchemy async uchun uni `postgresql+asyncpg://` ga o'zgartirib, `DATABASE_URL` sifatida bot service'iga bering. Original (`postgresql://...`) qiymatni esa `SYNC_DATABASE_URL` sifatida bering — bu `pg_dump` backup uchun kerak.

**b) Bot service**
Railway dashboard → *New* → *GitHub Repo* (yoki *Empty Service* + CLI orqali deploy).

### 2. Environment Variables (bot service)

`.env.example` dagi barcha o'zgaruvchilarni Railway → *Variables* bo'limiga kiriting:

```
BOT_TOKEN=...
BOT_USERNAME=...
SUPERADMIN_IDS=...
USE_WEBHOOK=true
WEBHOOK_HOST=https://<railway-domain>.up.railway.app
DATABASE_URL=postgresql+asyncpg://...   (Postgres service'dan, prefiksni asyncpg'ga o'zgartiring)
SYNC_DATABASE_URL=postgresql://...      (Postgres service'dan, o'zgarishsiz)
BACKUP_CHANNEL_ID=-100...
```

### 3. Deploy

`Procfile` va `railway.json` allaqachon tayyor:
- **release** bosqichida `alembic upgrade head` avtomatik ishlaydi (deploy paytida, ma'lumot yo'qolmaydi)
- **web** bosqichida bot webhook serverini ishga tushiradi

Railway avtomatik domen beradi — shu domenni `WEBHOOK_HOST` ga qo'ying va qayta deploy qiling.

### 4. Botni kanallarga admin qilib qo'ying

Majburiy kanal biriktirishdan oldin bot shu kanalda **admin** bo'lishi shart (`get_chat_member` orqali tekshiriladi).

---

## 🗄 Persistent Database

- Barcha ma'lumotlar **faqat PostgreSQL'da** saqlanadi — lokal JSON yoki fayl ishlatilmagan.
- `Base.metadata.drop_all()` hech qayerda chaqirilmagan.
- Har deployda `alembic upgrade head` ishlaydi — bu **ma'lumotni o'chirmasdan** sxema yangilaydi.
- Restart yoki qayta deploy bo'lganda — barcha userlar, referrallar, konkurslar saqlanib qoladi.

---

## 🔁 Background vazifalar (APScheduler)

| Vazifa | Interval | Nima qiladi |
|---|---|---|
| `contest_auto_transition` | 1 daqiqa | `scheduled → active`, `active → ended` |
| `recheck_subscriptions` | `.env`: `SUBSCRIPTION_RECHECK_INTERVAL_HOURS` (default 1 soat) | obunani qayta tekshiradi, chiqib ketganlarning referralini bekor qiladi |
| `create_backup` | `.env`: `BACKUP_INTERVAL_HOURS` (default 24 soat) | `pg_dump` orqali backup yaratadi, yopiq Telegram kanaliga yuboradi |

---

## 🧩 Kengaytirish

- Yangi rol qo'shish → `app/filters/role_filter.py` va `RoleMiddleware` ni kengaytiring
- Yangi konkurs turi (masalan ball tizimi boshqacha) → `RatingService` ni meros oling
- Redis kerak bo'lsa (masalan FSM storage uchun productionda) → `requirements.txt` da allaqachon bor, `MemoryStorage` ni `RedisStorage` ga almashtiring
