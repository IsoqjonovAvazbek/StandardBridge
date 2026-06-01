# StandardBridge — Claude Code Memory

## Loyiha haqida
Django 6.0.5 B2B startup — O'zbekistondagi korxonalarni ISO/CE/EN sertifikatlash uchun AI gap analiz + tasdiqlangan mutaxassislar + escrow to'lov platformasi.

## Stack
- Backend: Django 6.0.5, SQLite
- Frontend: Tailwind CSS (CDN), vanilla JS
- AI: Groq API (llama-3.3-70b-versatile)
- Auth: Custom AbstractUser (roles: entrepreneur, expert, admin)

## Apps
- `accounts` — foydalanuvchilar, rollar, admin panel, referral, til o'zgartirish
- `analysis` — gap analysis, AI, roadmap, sanoat/standartlar
- `experts` — loyihalar, to'lovlar, hamyon, reytinglar, bildirishnomalar
- `blog` — maqolalar (Category + BlogPost)
- `qms` — QMS Tool: checklist, hujjatlar, nomuvofiqliklar, audit jadvali
- `expert_tools` — Expert Tools: AI hujjat generatori, audit checklist, loyiha shablonlari, CRM

## Key models
- `CustomUser`: role, company_name, phone, region, industry, referral_code, referred_by
- `ExpertProfile`: bio, specializations, rating, is_verified, is_available, project_price
- `EntrepreneurProfile`: company_description, employee_count, export_experience
- `GapAnalysis`: entrepreneur, local_standard, target_standard, industry, ai_result (JSON), status
- `GapItem`: analysis, title, priority (critical/high/medium/low), estimated_days
- `Roadmap` + `RoadmapStep`: is_completed toggle (AJAX)
- `Project`: entrepreneur, expert, status (pending→negotiating→in_progress→review→completed), sla_hours/sla_deadline/sla_status
- `Payment`: escrow (held→released), 20% platform fee, 80% expert
- `BlogPost`: slug, content, is_published, views_count
- `Notification`: user, is_read (badge in sidebar)

## Key URLs
- `/` — landing
- `/register/` — ro'yxatdan o'tish (referral_code qabul qiladi)
- `/accounts/login/` — kirish
- `/analysis/` — entrepreneur dashboard
- `/experts/dashboard/` — expert dashboard
- `/admin-panel/` — custom admin panel
- `/blog/` — blog list
- `/referral/` — referral sahifasi
- `/set-language/` — til o'zgartirish (POST)
- `/experts/click/prepare/` va `/experts/click/complete/` — Click webhook

## Ko'p til tizimi
- Session-based: `request.session['lang']` = 'uz'|'ru'|'en'
- `core/context_processors.py`: `language_context` → `T` dict, `current_lang`, `langs`
- `core/translations.py`: TRANSLATIONS dict 200+ kalit (UZ/RU/EN to'liq)
- Templatelarda: `{{ T.dashboard }}`, `{{ T.login }}` etc.
- **TO'LIQ BAJARILGAN** — barcha sahifalar (landing, login, register, dashboardlar, analysis, roadmap, experts, blog, referral, wallet, notifications, profile) T.* ishlatadi

## Bajarilgan features
### Priority 1 (ZARUR)
- [x] Click payment webhook (mock + real endpoint)
- [x] Expert reyting UI (leave_review, star rating)
- [x] Expert verifikatsiya (admin panel + is_verified filter)
- [x] Email bildirishnomalar (6 ta funksiya, Gmail SMTP)
- [x] Landing page (to'liq qayta yozilgan)

### Priority 2 (MUHIM)
- [x] Async AI (threading, AJAX polling, processing.html)
- [x] Roadmap qadam toggle (AJAX, progress bar)
- [x] Expert search/filter (region, rating, price, sort)
- [x] Admin panel (statistika, Chart.js grafiklari)
- [x] Mobile responsiveness (hamburger, sidebar slide)

### Priority 3 (O'SISH)
- [x] Blog/maqolalar app
- [x] Referral tizimi (referral_code, referred_by, sahifa)
- [x] Ko'p til tizimi (UZ/RU/EN — TO'LIQ, barcha sahifalar)
- [x] Admin Chart.js (6 oylik foydalanuvchi + daromad grafiklar)

### Qo'shimcha features
- [x] Tadbirkor profil sahifasi (/profile/)
- [x] Admin expert inline tasdiqlash (Tasdiqlash tugmasi)
- [x] Bildirishnoma badge (unread count)
- [x] except: bare → aniq exception
- [x] SECRET_KEY → .env
- [x] SLA tizimi: Project.sla_hours/sla_deadline/sla_status, check_sla management command, expert_dashboard countdown timer, project_list SLA badge
- [x] Huquqiy disclaimer tizimi: DisclaimerAcceptance model (user, accepted_at, ip, version), modal blocker analysis_detail.html da, /analysis/disclaimer/accept/ endpoint, footer notice
- [x] Expert Tools app: 7 model (DocumentTemplate, GeneratedDocument, AuditChecklist, AuditChecklistItem, ProjectTemplate, ProjectTemplateStep, ClientCRM, CRMNote), 21 URL, 10 template, UZ/RU/EN translations, sidebar link, /expert-tools/

### MVP 10 ta savol (TO'LIQ bajarilgan)
- [x] 1. Hamyondan pul yechish: WithdrawalRequest model (mablag'ni darrov rezerv qiladi, rad etilsa qaytaradi), wallet.html form + tarix, admin_process_withdrawal
- [x] 2. Click to'lov ishlashi (mavjud webhook)
- [x] 3. SLA timeout oqibatlari (SLA tizimi + badge)
- [x] 4. Sertifikatsiya organlari yo'riqnomasi: analysis_detail.html da "Sertifikatsiya organlari" bo'limi (UZSTANDARD, Bureau Veritas, SGS, TÜV, IsoSert)
- [x] 5. Expert sertifikat verifikatsiyasi: ExpertProfile.cert_number/issuing_body/cert_expiry, expert_profile_edit form, admin_panel ko'rsatadi
- [x] 6. Nizo mexanizmi: Dispute model, open_dispute (entrepreneur), admin_resolve_dispute, project_detail + admin_panel UI
- [x] 7. Kompaniya scope expertga ko'rinadi: project_detail.html company scope card (entrepreneur_profile)
- [x] 8. Expert AI roadmap tahrirlashi: add_roadmap_step / delete_roadmap_step, project_detail modal
- [x] 9. Real-time bildirishnomalar (Notification + email funksiyalar)
- [x] 10. AI hujjat til tanlovi: generate_document language param (uz/ru/en), documents.html select
- [x] AI hujjat markdown render: document_detail.html client-side JS markdown parser (**bold**, sarlavha, ro'yxat, jadval → HTML; raw textarea copy uchun)

### Bug fixes (real test bilan topilgan)
- [x] experts/views.py wallet withdraw: `Decimal - float` TypeError → Decimal(str()) + InvalidOperation (pul yechishda crash edi)
- [x] qms/views.py silent failures: add_nonconformity / add_audit / upload_document / update_document_version endi messages.success/error beradi (avval jim redirect edi, foydalanuvchiga feedback yo'q edi)

### QMS mukammallashtirildi (4 ta yangi imkoniyat)
- [x] AI yordamchi: ai_nc_suggestion (NC uchun tub sabab + tuzatuvchi chora, AJAX) + qms_generate_policy (AI ISO siyosat/protsedura yozadi, .md fayl sifatida QMSDocument ga saqlanadi). nonconformities.html ✨ tugma, documents.html AI modal
- [x] NC raqamlari + overdue: NonConformity.code (NC-2026-001, _next_nc_code per-company/yil), NonConformity.is_overdue + AuditSchedule.is_overdue property, qizil "Muddati o'tgan" badge
- [x] Eksport: export_checklist_csv / export_nc_csv (Excel-mos UTF-8 BOM CSV), checklist va NC sahifalarida "Excel yuklash" tugma
- [x] Hujjat muddati eslatma: QMSDocument.expiry_notified + is_expired/days_to_expiry, check_document_expiry management command (Notification + email, takror yubormaydi, --days/--reset), documents.html da muddat badge (orange <=30 kun, qizil tugagan)
- [x] qms migration 0004 (NC code, ai_suggestion, expiry_notified)

### Tahlil (gap-analiz) mukammallashtirildi — loyihaning yuragi
- [x] Korxona konteksti → AI: answer_questions.html da kontekst bloki (xodimlar soni, eksport bozorlari, mavjud sertifikatlar, hozirgi holat), session['company_context'], _build_company_context(), GapAnalysis.company_info ga saqlanadi va AI promptiga uzatiladi
- [x] Tayyorlik foizi (readiness): _compute_readiness() (yes=1.0/partial=0.5/no=0.0), analysis_detail.html SVG gauge + prioritet breakdown (critical/high/medium/low), AI promptiga ham uzatiladi
- [x] Ko'p tilli AI: AI_LANG_INSTRUCTION (uz/ru/en), get_ai_analysis(language=) — gaps/roadmap/summary foydalanuvchi tilida
- [x] Ishonchli JSON: _extract_json() (``` fence + regex {...} fallback), gap/roadmap yaratish .get() default bilan (KeyError crash yo'q), priority validatsiya
- [x] Retry: analysis_retry view + _relaunch_analysis() (DB dan javoblarni qayta o'qiydi, ish yo'qolmaydi), processing.html error-box + has_error (analysis_status JSON), poll endi /analysis/new/ ga redirect qilmaydi
- [x] PDF eksport: analysis_print view + analysis_print.html (chop etish/PDF, readiness, gaps jadval, roadmap, cost_breakdown), analysis_detail.html da "PDF yuklash" tugma
- [x] cost_breakdown: AI estimated_cost ni consulting + certification_body ga ajratadi, detail va print da ko'rsatiladi
- [x] core/translations.py: ctx_*, readiness_label, analysis_export_pdf, analysis_error_*, analysis_retry_btn, cost_*, summary_label, gap_title_col, priority_col (UZ/RU/EN)

### Tahlil — 3 ta qo'shimcha (ketma-ket bajarildi, real test)
- [x] ISO 22000/14001/45001 savollari: seed_questions har standartga 12 ta savol yukladi (avval faqat ISO 9001 da savol bor edi). Endi 4 standart ham to'liq tahlil qiladi
- [x] Readiness taqqoslash: analysis_detail readiness_delta/prev_readiness (oldingi completed tahlil bilan solishtiradi), ▲+/▼- badge, readiness_vs_prev/readiness_no_change (UZ/RU/EN)
- [x] AI gaps → QMS: gaps_to_qms view (/analysis/<pk>/to-qms/), GapItem → NonConformity (priority→severity: critical→critical, high→major, medium/low→minor, _next_nc_code, title bo'yicha duplikat oldini oladi), analysis_detail "Nomuvofiqliklarni QMS ga ko'chirish" tugma, gaps_to_qms_* tarjimalar

### Tahlil ↔ Expert Tools integratsiyasi (A+B, real test)
- [x] A: expert project_detail.html da mijoz tahlili (gaplar + roadmap) allaqachon ko'rinadi (project.analysis orqali)
- [x] B: audit_from_analysis view (/expert-tools/audit/from-analysis/<project_id>/) — mijoz gap-analizidan professional AuditChecklist yaratadi. Har gap → AuditChecklistItem (status=non_compliant, finding=gap.description, prioritet bo'yicha tartib), target_standard kodidan iso9001/22000/14001/45001 aniqlanadi. project_detail "Tahlildan audit checklist yaratish" tugma (expert + gaps bo'lsa), audit_from_analysis_* tarjimalar (UZ/RU/EN)

### Production xavfsizligi + ro'yxatdan o'tish (1-daraja, real test)
- [x] register_view validatsiya: bo'sh ism/familiya/username/email/rol tekshiruvi (avval first_name None bo'lsa 500 crash edi), parol >=8 belgi, password2 mos kelishi, form_data bilan kiritilgan ma'lumot saqlanadi. register.html ga password2 maydon + qiymatlarni saqlash. password_confirm/password_hint tarjimalar
- [x] settings.py: DEBUG/ALLOWED_HOSTS env-driven (.env dan), DEBUG=False bo'lsa SECURE_SSL_REDIRECT/SESSION_COOKIE_SECURE/CSRF_COOKIE_SECURE/HSTS/nosniff/X_FRAME_OPTIONS/CSRF_TRUSTED_ORIGINS. .env ga DEBUG/ALLOWED_HOSTS/CSRF_TRUSTED_ORIGINS namuna
- [NOTE] Click to'lov: kod tayyor, lekin CLICK_SERVICE_ID/MERCHANT_ID/SECRET_KEY my.click.uz dan olinishi kerak (biznes registratsiya)

### Tahlil jonli ish maydoni (2-daraja, real test)
- [x] gap_toggle_resolved view (/analysis/<pk>/gap/<gap_pk>/toggle/) — GapItem.is_resolved AJAX toggle (avval ishlatilmas edi). analysis_detail.html: har gap yonida checkbox, line-through, progress bar (resolved_count/gaps_total/resolved_pct), begona user 404. gap_resolved_label/gap_mark_resolved tarjimalar (UZ/RU/EN)

### Avtomatlashtirilgan testlar (Django TestCase, 36 ta test — hammasi OK)
- [x] accounts/tests.py (9): register validatsiya (bo'sh ism crash yo'q, parol >=8, password2, dublikat, noto'g'ri rol), login
- [x] experts/tests.py (7): hamyon pul yechish (rezerv, balansdan ko'p rad, harf=crash yo'q, kartasiz rad), admin tasdiqlash/rad (refund)
- [x] qms/tests.py (8): NC kod generatsiya + increment, bo'sh forma silent-fail yo'q, overdue property, CSV eksport, hujjat muddati
- [x] analysis/tests.py (9): _compute_readiness, _extract_json (fence/prose/invalid), gap toggle (resolve/revert/begona 404), gaps→QMS (severity map + duplikat yo'q)
- [x] expert_tools/tests.py (3): audit_from_analysis (gaps→checklist, ISO22000→iso22000, critical birinchi, begona expert 404)
- Ishga tushirish: `python manage.py test` (yoki bitta app: `python manage.py test accounts`)

## Git + GitHub (professional workflow)
- [x] git repo init + .gitignore (.env, venv, db.sqlite3, logs/, media/ himoyalangan)
- [x] .env.example (kalitsiz namuna), README.md (ishga tushirish yo'riqnomasi), requirements.txt tuzatildi (UTF-16 → UTF-8, groq/dotenv qo'shildi)
- [x] GitHub remote: https://github.com/Avazbek-1/StandardBridge (private), branch=main
- Workflow: kod → `python manage.py test` → user brauzerda tekshiradi → user "push qil" deydi → push. Credential Windows Credential Manager da saqlangan
- ⚠️ GROQ_API_KEY avval oshkor bo'lgan — console.groq.com da yangilash tavsiya etiladi

## Production tayyorlash (universal, har hostingga mos)
- [x] 1-qadam: LOGGING (core/settings.py — console + logs/app.log + logs/error.log, RotatingFileHandler 5MB). AI xato bloklari logger.exception bilan yoziladi (analysis/qms/expert_tools, logger=getLogger('standardbridge')). WhiteNoise middleware + CompressedManifestStaticFilesStorage (STORAGES). collectstatic OK (650 fayl)
- [x] 2-qadam: check --deploy — DEBUG=False + kuchli SECRET_KEY bilan 0 ogohlantirish (settings xavfsizligi tayyor: HSTS/secure cookies/SSL redirect ishlaydi). README ga production deploy bo'limi (SECRET_KEY generatsiya, check --deploy, collectstatic, migrate). PROD uchun .env: DEBUG=False, kuchli SECRET_KEY, ALLOWED_HOSTS, CSRF_TRUSTED_ORIGINS kerak

## PENDING (bajarilmagan)
- [x] QMS tool — TO'LIQ bajarilgan (checklist ISO9001/22000/14001/45001, hujjatlar, NC, audit)
- [x] Expert Tools — TO'LIQ bajarilgan (AI doc generator, audit checklist, project templates, CRM — /expert-tools/)
- [ ] Auditor mobile checklist tool
- [ ] Payme integratsiya (Click bor, Payme yo'q)
- [ ] Ko'p tillar uchun email shablonlar

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

## Context window tugaganda davom etish
1. `/compact` buyrug'ini ishlatish
2. Yangi sessiyada: "CLAUDE.md ni o'qi va [qaysi task] dan davom et"
3. Yoki: "PENDING bo'limidagi birinchi taskdan boshlаgin"
 va har bir o'zgarishdan keyin claude.md file ga ham o'zgarishlarni yozib qoy
