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

### QMS — 1-yo'nalish to'liq (menejer/sifat bo'limi uchun, ISO sertifikatsiyaga tayyor)
- [x] Risk Register: RiskItem model (likelihood×impact matrix, risk_level critical/high/medium/low, mitigation, owner, due_date, is_overdue), risk_register.html (jadval+filtrlash+modal+Excel), ISO 9001/14001/45001 §6.1 talabini qoplaydi
- [x] Training Records: TrainingRecord model (xodim, lavozim, trening nomi, ISO band, sertifikat raqami, expiry_date, is_expired/days_to_expiry), training_records.html (jadval+alertlar+modal+Excel), ISO 9001 §7.2 talabini qoplaydi
- [x] NC Effectiveness Verification: NonConformity ga is_effective_verified+verification_note+verified_at, nonconformities.html da yopilgan NC uchun "Samaradorligini tasdiqlash" tugma+forma (ISO 10.2.1)
- [x] QMS Health Score dashboard: Weighted score (checklist 40% + NC yopish 30% + hujjat validligi 20% + audit jadval 10%), SVG gauge, rangkod (yashil/sariq/qizil)
- [x] Dashboard: Risk va Training mini-kartalar (open_risks, expiring_trainings alertlar)
- [x] qms/admin.py: RiskItem, TrainingRecord, NonConformity admin registratsiyasi
- [x] migration 0005

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

### Roadmap qadamlari bazadan (AI tegmaydi)
- [x] StandardRoadmapStep model (Standard FK, order, title, description, deliverables JSONField, duration_days, is_active). migration 0007
- [x] seed_roadmap_steps management command: ISO 9001/14001/45001/22000 uchun jami 163 ta tayyor qadam bazaga yuklandi (idempotent)
- [x] get_ai_analysis: DB roadmap yuklash promptdan OLDIN bajariladi. has_db_roadmap=True bo'lsa prompt JSON shablonidan roadmap_steps bloki olib tashlanadi va AI ga "sen tegma" qoidasi yoziladi. AI faqat gap izohlari + summary yozadi
- [x] StandardRoadmapStep Django admin ga qo'shildi (list_editable: order/duration_days/is_active)
- [x] start.sh ga seed_roadmap_steps qo'shildi (Railway Postgres da ham yuklangani uchun)

### Avtomatlashtirilgan testlar (Django TestCase, 60 ta test — hammasi OK)
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
- [x] 3-qadam: AI timeout — settings.AI_TIMEOUT (default 45s, .env dan sozlanadi). 3 ta Groq chaqiruvi (analysis/qms/expert_tools) endi Groq(timeout=settings.AI_TIMEOUT, max_retries=1) — sekin javobda cheksiz kutmaydi. .env.example ga AI_TIMEOUT qo'shildi
- [x] 4-qadam: Custom error sahifalar — templates/404.html, 500.html, 403.html (mustaqil, base.html'siz, inline Tailwind — 500 da context processor ishlamasligi uchun). UZ/RU/EN matn, "Bosh sahifaga qaytish" tugma, brend gradient. DEBUG=False da test: 404 to'g'ri ishladi, hammasi standalone render OK
- [x] 5-qadam: Deploy fayllari — Procfile (release: migrate + web: gunicorn core.wsgi --workers 3 --timeout 120), runtime.txt (python-3.12.7), requirements.txt ga gunicorn/whitenoise/dj-database-url/psycopg2-binary qo'shildi. settings.py: DATABASE_URL env bo'lsa Postgres (dj_database_url.parse, conn_max_age=600), bo'lmasa SQLite. .env.example + README ga deploy bo'limi. 36 test OK. (gunicorn faqat Linux/serverda ishlaydi, Windows lokalda emas)

## Railway deploy (BAJARILDI — sayt online: standardbridge.up.railway.app)
- [x] GitHub repo Railway ga ulandi, Postgres qo'shildi, DATABASE_URL=${{Postgres.DATABASE_URL}} web service ga bog'landi
- [x] Env vars: SECRET_KEY (kuchli), DEBUG=False, ALLOWED_HOSTS, CSRF_TRUSTED_ORIGINS, GROQ_API_KEY, MISE_PYTHON_GITHUB_ATTESTATIONS=false (build fix)
- [x] CSRF_TRUSTED_ORIGINS endi DEBUG dan qat'i nazar qo'llanadi + SECURE_PROXY_SSL_HEADER (proxy HTTPS)
- [x] .gitattributes: Procfile/runtime/requirements eol=lf (Railway CRLF o'qiy olmaydi)
- [x] Railway Custom Start Command: migrate + collectstatic + seed_data + seed_questions + load_checklist + gunicorn (Procfile web: ham shu)
- [x] seed_data management buyrug'i (analysis): 11 sanoat + 8 standart yuklaydi (idempotent get_or_create) — "Sohalar topilmadi" muammosi shu bilan hal bo'ldi (Postgres bo'sh edi)
- [x] To'liq tizim testi: register (entrepreneur+expert, profil yaratiladi), soha/standart tanlash, dashboard/analysis/qms/expert-tools/admin-panel — hammasi 200/302 OK
- [x] AI tahlil production'da ishladi (GROQ_API_KEY Railway Variables ga yangi kalit qo'yilgach — eski 401 Invalid API Key edi). Logging xatoni aniq ushladi
- [x] seed_experts management buyrug'i (accounts): har viloyat uchun 1 ta demo tasdiqlangan expert (13 ta, user+ExpertProfile, is_verified=True, login: expert_<region>/demo12345, idempotent). Procfile web: ga qo'shildi. "Hali mutaxassis yo'q" muammosi hal bo'ldi
- [x] 5-qadam: Deploy fayllari — Procfile (release: migrate + web: gunicorn core.wsgi --workers 3 --timeout 120), runtime.txt (python-3.12.7), requirements.txt ga gunicorn/whitenoise/dj-database-url/psycopg2-binary qo'shildi. settings.py: DATABASE_URL env bo'lsa Postgres (dj_database_url.parse, conn_max_age=600), bo'lmasa SQLite. .env.example + README ga deploy bo'limi. 36 test OK. (gunicorn faqat Linux/serverda ishlaydi, Windows lokalda emas)

### Login soddalashtirildi (rol tanlovsiz)
- [x] Login'dan rol tanlash (Tadbirkor/Mutaxassis tugmalari) OLIB TASHLANDI — login.html va login_view. Tizim username/paroldan rolni o'zi aniqlaydi va dashboard view orqali to'g'ri sahifaga yo'naltiradi (entrepreneur→/analysis/, expert→/experts/dashboard/, admin→/admin-panel/)
- [x] Registratsiyada rol tanlash QOLADI (Tadbirkor/Mutaxassis + mos maydonlar) — bu yerda foydalanuvchi kim ekanini belgilaydi
- [x] accounts/tests.py: test_login_no_role_needed_redirects_by_role qo'shildi (10 test)

### Biznes-mantiq xatolari tuzatildi (real test bilan topilgan)
- [x] project_detail.html: dispute-modal + add-step-modal {% block content %} dan TASHQARIDA edi (render bo'lmasdi → tugmalar ishlamasdi). {% endblock %} modallardan keyinga ko'chirildi
- [x] project_request_revision view + URL + modal: entrepreneur ishni qabul qilmay qayta ishlashga qaytaradi (review→in_progress, sabab majburiy, expertga notif). Avval faqat "Qabul qilish" bor edi — adolatsiz
- [x] project_complete guard: roadmap bor + hech qadam bajarilmagan bo'lsa yakunlab bo'lmaydi (expert ish qilmasdan "yakunladim" deya olmaydi)
- [x] payment_release guard: ochiq nizo (dispute open/in_review) bo'lsa pul bloklanadi (admin hal qilmaguncha)
- [x] project_set_price guard: faqat pending/negotiating da narx belgilanadi (to'lovdan keyin o'zgartirib bo'lmaydi) + float/int ValueError tuzatildi (crash yo'q, price/days > 0 tekshiruvi)
- [x] experts/tests.py: ProjectLifecycleTests (7 test) — revision, dispute bloklash, complete guard, set_price guard. Jami 44 test OK
- [x] request_revision_* tarjimalar (UZ/RU/EN)

### Biznes-mantiq — 2-to'plam (status guard + roadmap vaqt)
- [x] project_accept guard: faqat negotiating statusdagi loyihani qabul qilish mumkin (completed/in_progress ni qayta accept qilib bo'lmaydi)
- [x] leave_review: rating int() ValueError fix + 1..5 oralig'iga cheklash (harf/chegaradan tashqari crash yo'q)
- [x] edit_roadmap_step view + URL + modal: expert mavjud qadam nomi/tavsifi/vaqtini aniqlashtiradi (AI taxminini tuzatadi), roadmap.total_days qayta hisoblanadi, entrepreneur 404
- [x] roadmap.html: "Vaqt va xarajat AI taxmini, mutaxassis aniqlashtiradi" izohi (roadmap_ai_estimate_note, UZ/RU/EN) — tadbirkor AI vaqtini aniq muddat deb o'ylamasligi uchun
- [x] edit_step_* tarjimalar. 44 test OK

### Ruxsat va input audit (3-to'plam)
- [x] expert_profile_edit + entrepreneur profile: int/Decimal ValueError himoyasi (harf kiritilsa crash emas, 0 ga tushadi)
- [x] Admin panel ruxsati tasdiqlandi (admin_panel/verify/withdrawal/dispute hammasi is_staff||is_admin tekshiradi). AdminPanelAccessTests (3 test): entrepreneur/expert 302, admin 200
- [x] gaps_to_qms/audit_from_analysis ruxsati tasdiqlandi (entrepreneur=request.user / expert=request.user — begona 404, allaqachon test bor)
- [x] Jami 47 test OK. Butun int/float input himoyalandi (price/days/rating/experience/employee_count)

### Real foydalanuvchi UX xatolari (real test bilan, autonom)
- [x] Sayt qotishi (tahlil yuborish/narx belgilash/to'lov): experts/emails.py _send endi background thread (Gmail SMTP sinxron edi -> 30-60s qotardi). Endi so'rov darrov javob beradi, email orqada ketadi
- [x] Audit foizlari real vaqtda: audit_detail.html score-ring/score-text/score-count ID lar + update_audit_item compliant/total qaytaradi, JS halqa+foiz+hisobni refreshsiz yangilaydi
- [x] Chat real vaqtda: project_messages JSON endpoint (?after=id), project_update AJAX (X-Requested-With) JSON qaytaradi, project_detail.html chat AJAX submit + 5s polling (sahifa qayta yuklanmaydi)
- [x] Expert profil narx/vaqt: project_price_stat/duration_stat -> "boshlang'ich narx / o'rtacha muddat" + "har loyiha alohida kelishiladi" izohi (chalkashlik yo'q)
- [x] Loyiha shablonlari: Procfile ga load_expert_templates qo'shildi (Postgres da bo'sh edi)
- [x] price_note_per_project tarjimalar (UZ/RU/EN). 47 test OK

### Tarjima + real-time + roadmap mukammallashtirish (autonom)
- [x] Model choices tarjimasi: core/translations.py CHOICE_LABELS (status/severity/priority/audit_type/doc_type — UZ/RU/EN), get_choice_label, accounts/templatetags/labels.py {% label code %} tag. 14 ta template get_*_display -> {% label %} (RU/EN da o'zbekcha chiqmasdi)
- [x] QMS checklist real-time foiz: update_checklist pct/compliant/total qaytaradi, JS progress bar + tab foizini refreshsiz yangilaydi (progress-pct/bar/compliant, tab-pct-<std>)
- [x] Roadmap kun olib tashlandi (tadbirkor): roadmap.html da har qadam duration_days -> "Bosqich N" (kunni expert belgilaydi, AI taxmini chalkash edi). Umumiy est_time_label qoldi
- [x] Roadmap batafsilroq: RoadmapStep.deliverables (JSONField), AI prompt 5-8 batafsil bosqich + deliverables so'raydi, roadmap.html + project_detail.html da "Tayyorlanadigan hujjatlar" bloki. migration 0005
- [x] step_word/step_deliverables_lbl tarjimalar. 47 test OK

### Expert Tools mukammallashtirish (real muammolar hal qilindi)
- [x] Proposal Generator: Proposal model (company, standard, scope, price_min/max, duration_days, content, status, valid_until), AI taklifnoma generatsiyasi (Groq), list/detail/edit/delete views, proposal_print.html (PDF, imzolar), status workflow (draft→sent→accepted/rejected)
- [x] Time Tracker: TimeLog model (expert, project, date, hours, description), add/delete views, time_logs.html (bu oy jami, loyiha bo'yicha breakdown, so'nggi 20 yozuv)
- [x] Earnings Dashboard: 6 oylik Chart.js bar chart, loyiha bo'yicha daromad breakdown, to'lovlar tarixi, bu oy soat+daromad
- [x] Audit PDF Hisobot: audit_print.html (professional: score boxes, asosiy topilmalar, to'liq checklist jadval, imzo joylari), audit_detail.html ga "PDF Hisobot" tugma
- [x] Dashboard yangilandi: yangi 3-quick action (taklifnomalar/vaqt/daromad), bugungi CRM follow-up alert bloki, month_hours/month_earnings context vars
- [x] migration 0002 (Proposal, TimeLog)

## PENDING (bajarilmagan)
- [x] Auditor mobile checklist tool — /audit/<pk>/mobile/ (kartadan karta, AJAX auto-save, real-time foiz)
- [ ] Payme integratsiya (Click bor, Payme yo'q)
- [x] Ko'p tillar uchun email shablonlar — CustomUser.preferred_language + 10 funksiya UZ/RU/EN

### Oxirgi sессiyada bajarilganlar (2026-06-05)
- [x] To'lov tugmasi bug: payment_page har doim Payment yaratadi (CLICK_SERVICE_ID bo'lsa ham bo'lmasa ham)
- [x] payment.html: `{% if debug %}` → `{% if not click_service_id %}` — Railway da to'lov ko'rinmas edi
- [x] Dashboard: accepted loyihalar uchun "To'lov qilish" CTA tugmasi qo'shildi
- [x] training_records, risk_register, earnings, time_logs, proposal_list: barcha hardcoded text T.* ga o'tkazildi
- [x] N+1, dead code, import tozalash (oldingi sessiya — cda17af, 7009b50)

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

---

---

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
