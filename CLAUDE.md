# StandardBridge — Claude Code Memory

## Loyiha haqida
Django 6.0.5 B2B startup — O'zbekistondagi korxonalarni ISO/CE/EN sertifikatlash uchun AI gap analiz + tasdiqlangan mutaxassislar + escrow to'lov platformasi.

## Stack
- Backend: Django 6.0.5, SQLite (local) / PostgreSQL (Railway)
- Frontend: Tailwind CSS (CDN), vanilla JS
- AI: Groq API (llama-3.3-70b-versatile)
- Auth: Custom AbstractUser (roles: entrepreneur, expert, admin)
- Deploy: Railway — sayt: standardbridge.up.railway.app

## Apps
- `accounts` — foydalanuvchilar, rollar, admin panel, referral, til o'zgartirish
- `analysis` — gap analysis, AI, roadmap, sanoat/standartlar, savollar
- `experts` — loyihalar, to'lovlar, hamyon, reytinglar, bildirishnomalar
- `blog` — maqolalar (Category + BlogPost + BlogComment + BlogLike)
- `qms` — QMS Tool: checklist, hujjatlar, nomuvofiqliklar, audit jadvali, risk, training
- `expert_tools` — Expert Tools: AI hujjat, audit checklist, loyiha shablonlari, CRM, taklifnoma, vaqt

## Key models
- `CustomUser`: role, company_name, phone, region, industry, referral_code, referred_by, telegram_chat_id, is_email_verified
- `ExpertProfile`: bio, specializations, rating, is_verified, is_available, project_price, cert_number/issuing_body/cert_expiry
- `EntrepreneurProfile`: company_description, employee_count, export_experience
- `Industry`: name/name_ru/name_en, description/description_ru/description_en, icon, order — `get_name(lang)`, `get_description(lang)`
- `Standard`: code, name/name_ru/name_en, type (local/international), description/description_ru/description_en, industry FK — `get_name(lang)`, `get_description(lang)`
- `Question`: standard FK, text/text_ru/text_en, help_text/help_text_ru/help_text_en, answer_type — `get_text(lang)`, `get_help(lang)`
- `GapAnalysis`: entrepreneur, local_standard, target_standard, industry, ai_result (JSON), status, language
- `GapItem`: analysis, title, priority (critical/high/medium/low), estimated_days, is_resolved, clause
- `Roadmap` + `RoadmapStep`: is_completed toggle (AJAX), deliverables (JSONField)
- `StandardRoadmapStep`: standard FK, order, title, description, deliverables, duration_days (163 ta tayyor qadam)
- `Project`: entrepreneur, expert, status (pending→negotiating→in_progress→review→completed), sla_hours/sla_deadline/sla_status, counter_rounds
- `Payment`: escrow (held→released), 20% platform fee, 80% expert
- `Dispute`: project, opened_by, status (open/in_review/resolved)
- `WithdrawalRequest`: expert, amount (darrov rezerv qilinadi)
- `BlogPost`: slug, content, is_published, is_featured, views_count
- `Notification`: user, is_read (badge in sidebar)
- `NonConformity`: code (NC-2026-001), severity, is_effective_verified
- `RiskItem`: likelihood×impact matrix, risk_level, mitigation, owner
- `TrainingRecord`: employee, training_name, iso_clause, expiry_date
- `AuditChecklist` + `AuditChecklistItem`: expert tools audit
- `Proposal`: company, standard, scope, price_min/max, duration_days, content, status, valid_until
- `TimeLog`: expert, project, date, hours, description
- `ClientCRM` + `CRMNote`: expert tools CRM
- `DisclaimerAcceptance`: user, version (1.0)

## Key URLs
- `/` — landing
- `/register/` — ro'yxatdan o'tish (referral_code qabul qiladi)
- `/accounts/login/` — kirish (tizim rolni o'zi aniqlab yo'naltiradi)
- `/analysis/` — entrepreneur dashboard
- `/analysis/select-industry/` → `/analysis/<id>/standards/` → `/analysis/<id>/questions/` → `/analysis/<id>/run/`
- `/analysis/<pk>/` — tahlil natijasi
- `/experts/dashboard/` — expert dashboard
- `/expert-tools/` — Expert Tools dashboard
- `/qms/` — QMS dashboard
- `/admin-panel/` — custom admin panel
- `/blog/` — blog list
- `/referral/` — referral sahifasi
- `/set-language/` — til o'zgartirish (POST)
- `/experts/click/prepare/` va `/experts/click/complete/` — Click webhook
- `/accounts/telegram/connect/` — Telegram ulash
- `/accounts/verify-email/<token>/` — email tasdiqlash

## Ko'p til tizimi
- Session-based: `request.session['lang']` = 'uz'|'ru'|'en'
- `core/context_processors.py`: `language_context` → `T` dict, `current_lang`, `langs`
- `core/translations.py`: TRANSLATIONS dict 280+ kalit (UZ/RU/EN to'liq)
- Templatelarda: `{{ T.key }}` pattern
- **DB content tarjimasi**: `Industry`/`Standard`/`Question` modellarida `*_ru`/`*_en` maydonlar bor. Views sessiondan `lang` o'qib har bir obyektga `display_name`, `display_description`, `display_text`, `display_help` attribut qo'shadi. Template: `{{ industry.display_name }}`, `{{ question.display_text }}`
- Standalone print templatelar (`audit_print.html`, `proposal_print.html`): `base.html` extend qilmaydi → `T` ni view'dan explicit uzatish kerak (`get_translation(lang)` import qilib)
- Model choices tarjimasi: `CHOICE_LABELS` dict + `get_choice_label()` + `{% label code %}` template tag (`accounts/templatetags/labels.py`)

## Migrations holati
- `analysis`: 0009_multilingual_fields (oxirgi)
- `accounts`: 0010 (telegram), 0011 (counter_rounds) (oxirgi)
- `experts`: tegishli migrationlar
- `qms`: 0005 (risk, training) (oxirgi)
- `expert_tools`: 0002 (Proposal, TimeLog) (oxirgi)
- `blog`: 0005 (indexes) (oxirgi)

## Testlar
- Jami: **81 ta test**, hammasi OK
- `python manage.py test` — hammasi
- `python manage.py test accounts` — bitta app

## Git + Deploy
- GitHub: https://github.com/Avazbek-1/StandardBridge (private), branch=main
- Railway auto-deploy: main ga push → avtomatik deploy
- `start.sh`: migrate → collectstatic → seed_data → seed_standards → seed_questions → load_checklist → load_expert_templates → seed_experts → seed_roadmap_steps → seed_blog_posts → create_admin → setup_telegram_webhook → gunicorn
- Credentials: Windows Credential Manager da saqlangan

## .env fayli
```
GROQ_API_KEY=gsk_02O2Ulf...
SECRET_KEY=django-insecure-standartbridge-secret-key-2026
EMAIL_HOST_USER=your_email@gmail.com
EMAIL_HOST_PASSWORD=your_app_password
CLICK_SERVICE_ID= (bo'sh)
CLICK_MERCHANT_ID= (bo'sh)
CLICK_SECRET_KEY= (bo'sh)
CLICK_RETURN_URL=http://127.0.0.1:8000
```

## Muhim texnik eslatmalar
- Django template `{% for x in "a b c" %}` — string ni BOSh JOY bo'yicha emas, BELGI bo'yicha iteratsiya qiladi. Progress bar widthlarini statik yozing
- Email jo'natish `threading.Thread` da — SMTP bloklanishi yo'q
- `templates/landing.html` 800+ qator — o'qishdan oldin `limit` bering
- AI timeout: `settings.AI_TIMEOUT` (default 45s, `.env` dan sozlanadi)
- `python manage.py check --deploy` — 0 ogohlantirish (DEBUG=False, kuchli SECRET_KEY bilan)
- Click webhook: IP whitelist `_CLICK_ALLOWED_IPS`, `sign_time` timestamp tekshiruvi (1 soat)
- QMS health score: checklist 40% + NC yopish 30% + hujjat validligi 20% + audit jadval 10%
- Readiness: yes=1.0 / partial=0.5 / no=0.0, `_compute_readiness()`
- AI roadmap: DB `StandardRoadmapStep` dan yuklash prioriteti (163 qadam ISO 9001/14001/45001/22000 uchun)
- ⚠️ GROQ_API_KEY avval oshkor bo'lgan — console.groq.com da yangilash kerak

## Bajarilgan features (xulosa)
Barcha asosiy feature'lar to'liq ishlatilmoqda:
- Entrepreneur: soha tanlash → standart → savollar (UZ/RU/EN) → AI gap tahlil → roadmap → expert topish → loyiha → to'lov (escrow) → sertifikat
- Expert: dashboard → loyihalar → taklifnoma → audit → CRM → vaqt hisobi → daromad
- QMS: checklist → hujjatlar → NC → audit jadval → risk register → training records → health score
- Blog: maqolalar → like/komment → SEO
- Admin: foydalanuvchilar → expertlar tasdiqlash → to'lovlar → nizolar → statistika
- To'liq UZ/RU/EN (barcha template + DB content)
- Railway production online, 81/81 test OK

---

## HALI BAJARILMAGAN (PENDING)

### 🔴 KRITIK

1. **Sirlar yangilash (foydalanuvchi bajaradi)**
   - console.groq.com dan yangi GROQ_API_KEY olish
   - Yangi SECRET_KEY: `python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"`
   - `git rm --cached .env` — tarixdan o'chirish

2. **Click.uz real integratsiya**
   - CLICK_SERVICE_ID/MERCHANT_ID/SECRET_KEY hali bo'sh
   - `payment_confirm` MOCK transaction yaratadi — production da ishlamaydi
   - Click.uz da biznes ro'yxatdan o'tish kerak (1-2 kun)

3. **Payme integratsiya**
   - Hali amalga oshirilmagan (Click bor, Payme yo'q)

---

## Context window tugaganda davom etish
1. `/compact` buyrug'ini ishlatish
2. Yangi sessiyada: "CLAUDE.md ni o'qi va [qaysi task] dan davom et"
3. Yoki: "PENDING bo'limidagi birinchi taskdan boshlаgin"
4. Har bir muhim o'zgarishdan keyin CLAUDE.md yangilansin
