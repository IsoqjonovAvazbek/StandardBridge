# StandardBridge — Claude Code Memory

## ASOSIY QOIDA (MAJBURIY)
**Har bir bug, xatolik, mantiqiy xato yoki UX muammo topilganida:**
1. **Tuzat** — kodni to'g'irla
2. **Test qil** — `python manage.py test` ishga tushir, hammasi OK bo'lsin
3. **Push qil** — `git commit && git push origin main`

Ushbu tsikl har bir muammo uchun alohida bajarilsin. Yig'ib qo'yish yo'q.

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
- `Industry`: name/name_ru/name_en, description/description_ru/description_en, icon, order
- `Standard`: code, name/name_ru/name_en, type (local/international), description, industry FK
- `Question`: standard FK, text/text_ru/text_en, help_text, answer_type
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
- `/accounts/login/` — kirish
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
- **DB content tarjimasi**: `Industry`/`Standard`/`Question` modellarida `*_ru`/`*_en` maydonlar bor. Views sessiondan `lang` o'qib har bir obyektga `display_name`, `display_description`, `display_text`, `display_help` attribut qo'shadi.
- Standalone print templatelar (`audit_print.html`, `proposal_print.html`): `base.html` extend qilmaydi → `T` ni view'dan explicit uzatish kerak (`get_translation(lang)` import qilib)
- Model choices tarjimasi: `CHOICE_LABELS` dict + `get_choice_label()` + `{% label code %}` template tag (`accounts/templatetags/labels.py`)

## Ro'yxatdan o'tish (oxirgi holat)
- **username maydoni yo'q** — emaildan avtomatik hosil qilinadi (collision'da raqam qo'shiladi)
- Tadbirkor: faqat ism + email + parol
- Mutaxassis: ism + email + telefon + parol
- Region/sanoat/kompaniya nomi → profil sahifasida to'ldiriladi
- Referral kod: URL `?ref=` bo'lsa ko'rinadi, aks holda yashirin toggle

## Migrations holati
- `analysis`: 0009_multilingual_fields (oxirgi)
- `accounts`: 0010 (telegram), hech qanday yangi migration kerak emas
- `experts`, `qms`, `expert_tools`, `blog`: tegishli oxirgi migrationlar

## Testlar
- Jami: **83 ta test**, hammasi OK
- `python manage.py test` — hammasi
- `python manage.py test accounts` — bitta app

## Xavfsizlik — bajarilgan (2026-06 sessiya)
Commit tarixida: 603732d → e98ace7 → a4e7948 → 896a6b2 → dfe877f → cc1bb6e → 511d09b → bb4148a

### Auth va kirish
- `logout`: `@require_POST` (GET logout hujumidan himoya)
- `login_view`: `is_authenticated` tekshiruvi rate-limitdan OLDIN
- `register`: rate-limit (5/h email, 50/h IP)
- `resend_verification`: rate-limit (3/h user)
- `telegram_webhook`: production da SECRET majburiy

### To'lov va hamyon
- `payment_confirm`: MOCK faqat DEBUG=True yoki TESTING=True da
- `click_complete`: summa `payment.amount` ga teng bo'lishi tekshiriladi
- `payment_release`: wallet `get_or_create` keyin `select_for_update().get()` (race-safe)
- `scope_request_respond` accept: `Payment.amount += extra_price` atomik yangilanadi
- `admin_resolve_dispute` entrepreneur foydasiga: hamyonga qayt + WalletTransaction
- `admin_resolve_dispute`: `select_for_update()` ichida dispute re-fetch (ikki admin race)
- `withdrawal` reject: `WalletTransaction('refund')` yaratiladi (ledger to'liq)
- `project_request_revision`: roadmap faqat bu loyiha yagona bo'lsa resetlanadi

### Ma'lumot xavfsizligi
- `protected_media`: hujjat egasi tekshiriladi (IDOR)
- `project_set_price`: faqat expert roli
- `expert_detail`: `@login_required`
- `admin_process_withdrawal`: `card_number_plain` decrypt xatosi try/except
- `admin_resolve_dispute`: `select_for_update()` ichida re-fetch
- `leave_review`: `project.expert` NULL bo'lsa IntegrityError → guard qo'shildi (cc1bb6e)
- `resend_verification`, `telegram_connect/disconnect`: HTTP_REFERER open redirect → urlparse().path (511d09b)
- `SITE_URL`: settings.SITE_URL env var orqali (Railway da `SITE_URL=https://standardbridge.uz` qo'yish kerak)
- `DEFAULT_FROM_EMAIL`: noreply@standardbridge.uz (to'g'rilandi)
- `scope_request_respond`, `project_accept`, `project_counter_offer`: Notification user=project.expert null guard (bb4148a)
- `api_chatbot`: rate limit 20/m qo'shildi (bb4148a)
- Brand typo "StandartBridge" → "StandardBridge" (63 fayl, bb4148a)
- QMS + expert_tools AI prompt injection: _safe() sanitizatsiya qo'shildi (bb4148a)
- `scope_request_send`: faqat loyiha egasi

### Kod sifati
- `SECRET_KEY`: bo'sh bo'lsa `ImproperlyConfigured` (fallback yo'q)
- `DEBUG`: default `False` (`.env`da yoqilsin)
- `ALLOWED_HOSTS`: production da bo'sh, DEBUG=True da `['*']`
- `TESTING` flag: test paytida `DummyCache` (rate-limit testlar orasida saqlanmaydi)
- `GROQ_API_KEY`: `settings.GROQ_API_KEY` orqali (os.environ emas)
- `FERNET_KEY`: production da majburiy
- `EMAIL_BACKEND`: credentials sozlanmagan bo'lsa console backend (SMTP block yo'q)
- `PasswordResetView`: email background threadda yuboriladi

### Fayl va input
- `upload_document`: kontent-tur + kengaytma ikkalasi tekshiriladi
- `_next_nc_code`: company row `select_for_update()` bilan lock (duplikat NC oldini olish)
- `card_number`: 16-19 raqam (yuqori chegara qo'shildi)
- AI prompt: `_safe()` helper (injection oldini olish)
- `marked.parse → innerHTML`: DOMPurify.sanitize() bilan 5 ta templateda

### Rate-limiting
- login: 5/min IP
- register: 5/h email, 50/h IP  
- global_search: 30/min user
- add_comment: 10/min user
- resend_verification: 3/h user

### Ma'lumot yaxlitligi
- `analysis` background thread: faqat `status='pending'` loyihalar o'chiriladi
- `analysis_retake`: eski `local_ids`/`question_answers` sessiondan tozalanadi
- CSV eksport: `charset=utf-8` + BOM (ikki marta emas)
- `_click_ip_ok`: `X-Forwarded-For` ning oxirgi IP (proxy-safe)
- `Project.save()`: `Decimal` arifmetikasi (float emas)
- `Referral bonus bloki olib tashlandi` (referral tizimi o'chirildi)

## Git + Deploy
- GitHub: https://github.com/Avazbek-1/StandardBridge (private), branch=main
- Railway auto-deploy: main ga push → avtomatik deploy
- `start.sh`: migrate → collectstatic → seed_data → seed_standards → seed_questions → load_checklist → load_expert_templates → seed_experts → seed_roadmap_steps → seed_blog_posts → create_admin → setup_telegram_webhook → gunicorn

## .env fayli
```
GROQ_API_KEY=gsk_02O2Ulf...   ⚠️ YANGILASH KERAK
SECRET_KEY=django-insecure-standartbridge-secret-key-2026   ⚠️ YANGILASH KERAK
EMAIL_HOST_USER=your_email@gmail.com
EMAIL_HOST_PASSWORD=your_app_password
CLICK_SERVICE_ID= (bo'sh)
CLICK_MERCHANT_ID= (bo'sh)
CLICK_SECRET_KEY= (bo'sh)
CLICK_RETURN_URL=http://127.0.0.1:8000
```

## Muhim texnik eslatmalar
- Email jo'natish `threading.Thread` da — SMTP bloklanishi yo'q
- `templates/landing.html` 800+ qator — o'qishdan oldin `limit` bering
- AI timeout: `settings.AI_TIMEOUT` (default 45s, `.env` dan sozlanadi)
- Click webhook: IP whitelist `_CLICK_ALLOWED_IPS`, `sign_time` timestamp tekshiruvi (1 soat)
- QMS health score: checklist 40% + NC yopish 30% + hujjat validligi 20% + audit jadval 10%
- AI roadmap: DB `StandardRoadmapStep` dan yuklash prioriteti (163 qadam ISO 9001/14001/45001/22000 uchun)
- Gap Analysis savollar sahifasida "Korxona konteksti" yashirin (ixtiyoriy toggle) — AI prompta qo'shiladi agar to'ldirilsa

## Bajarilgan features
- Entrepreneur: soha tanlash → standart → savollar (UZ/RU/EN) → AI gap tahlil → roadmap → expert topish → loyiha → to'lov (escrow) → sertifikat
- Expert: dashboard → loyihalar → taklifnoma → audit → CRM → vaqt hisobi → daromad
- QMS: checklist → hujjatlar → NC → audit jadval → risk register → training records → health score
- Blog: maqolalar → like/komment → SEO
- Admin: foydalanuvchilar → expertlar tasdiqlash → to'lovlar → nizolar → statistika
- To'liq UZ/RU/EN (barcha template + DB content)
- Ro'yxatdan o'tish soddalashtirish: username olib tashlandi, maydonlar minimallashtirildi
- Entrepreneur dashboard soddalashtirish: trend grafigi olib tashlandi, ikkilanma onboarding tuzatildi, kompakt ko'rinish
- Railway production online, 83/83 test OK

---

## HALI BAJARILMAGAN (PENDING)

### 🔴 KRITIK (foydalanuvchi bajaradi)

1. **Sirlar yangilash**
   - Railway dashboard da yangilash:
     - `GROQ_API_KEY` → console.groq.com dan yangi kalit
     - `SECRET_KEY` → `python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"`
     - `EMAIL_HOST_USER` + `EMAIL_HOST_PASSWORD` → Gmail App Password (myaccount.google.com → Security → 2-Step → App passwords)
   - `.env` tarixdan o'chirish: `git rm --cached .env && echo ".env" >> .gitignore`

2. **Click.uz real integratsiya**
   - `CLICK_SERVICE_ID` / `CLICK_MERCHANT_ID` / `CLICK_SECRET_KEY` bo'sh
   - Click.uz da biznes ro'yxatdan o'tish kerak

3. **Payme integratsiya**
   - Hali amalga oshirilmagan

### 🟡 KEYINGI SESSIYADA
- Foydalanuvchi so'ragan chuqur pentest (professional pentest so'rov) — navbatdagi sessiyada davom etadi

---

## Context window tugaganda davom etish
1. `/compact` buyrug'ini ishlatish
2. Yangi sessiyada: "CLAUDE.md ni o'qi va [qaysi task] dan davom et"
3. Har bir muhim o'zgarishdan keyin CLAUDE.md yangilansin
