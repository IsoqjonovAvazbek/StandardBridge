# StandardBridge

O'zbekistondagi korxonalarni ISO/CE/EN sertifikatlashtirishga tayyorlash uchun B2B platforma:
**AI gap-analiz + tasdiqlangan mutaxassislar + escrow to'lov**.

## Stack
- **Backend:** Django 6.0.5, SQLite
- **Frontend:** Tailwind CSS (CDN), vanilla JS
- **AI:** Groq API (llama-3.3-70b-versatile)
- **Auth:** Custom AbstractUser (rollar: entrepreneur, expert, admin)

## Ilovalar
| Ilova | Vazifa |
|-------|--------|
| `accounts` | Foydalanuvchilar, rollar, admin panel, referral, til |
| `analysis` | Gap-analiz, AI, roadmap, sanoat/standartlar |
| `experts` | Loyihalar, to'lovlar, hamyon, reytinglar, bildirishnomalar |
| `qms` | QMS Tool: checklist, hujjatlar, nomuvofiqliklar, audit |
| `expert_tools` | AI hujjat generatori, audit checklist, shablonlar, CRM |
| `blog` | Maqolalar |
| `core` | Tarjimalar (UZ/RU/EN), context processors |

## Ishga tushirish

```bash
# 1. Virtual muhit
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # Linux/Mac

# 2. Kutubxonalar
pip install -r requirements.txt

# 3. Muhit o'zgaruvchilari
copy .env.example .env       # Windows  (cp .env.example .env — Linux/Mac)
# .env ni tahrirlang: GROQ_API_KEY va SECRET_KEY ni kiriting

# 4. Bazani tayyorlash
python manage.py migrate
python manage.py seed_questions        # tahlil savollari (ISO 9001/22000/14001/45001)
python manage.py load_checklist        # QMS checklist bandlari

# 5. Admin yaratish
python manage.py createsuperuser

# 6. Serverni ishga tushirish
python manage.py runserver
```

Sayt: http://127.0.0.1:8000

## Testlar

```bash
python manage.py test            # barcha testlar (36 ta)
python manage.py test accounts   # bitta ilova
python manage.py check           # tizim tekshiruvi
```

## Periodik vazifalar (cron / Task Scheduler)

```bash
python manage.py check_sla                # SLA muddatlari
python manage.py check_document_expiry    # hujjat muddati eslatmasi
```

## Muhim eslatmalar
- `.env` hech qachon git'ga qo'shilmaydi (maxfiy kalitlar)
- Loyiha xotirasi va to'liq feature ro'yxati: **CLAUDE.md**
- Click to'lov: kod tayyor, lekin `CLICK_*` kalitlar my.click.uz dan olinadi
