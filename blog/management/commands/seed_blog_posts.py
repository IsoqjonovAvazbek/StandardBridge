"""
Rasmiy manbalar asosida blog maqolalarini yuklaydi.

Manbalar:
  - ISO.org: "ISO 9001 - Quality management systems" (iso.org/iso-9001-quality-management.html)
  - UzDST: O'zbekiston Standartlashtirish, Metrologiya va Sertifikatsiya Agentligi (standart.uz)
  - European Commission: "CE marking" Blue Guide 2022 (single-market-economy.ec.europa.eu)
  - ITC (International Trade Centre): "Standards and quality infrastructure" (intracen.org)
  - UN/CEFACT: "Trade facilitation" guidelines
"""

from django.core.management.base import BaseCommand
from blog.models import BlogPost, Category


POSTS = [

    # ─────────────────────────────────────────────────────────────
    # ARTICLE 1 — ISO 9001:2015  (UZ)
    # ─────────────────────────────────────────────────────────────
    {
        'slug': 'iso-9001-2015-sertifikatsiya-qollanma-uz',
        'group_key': 'iso-9001-2015-certification-guide',
        'language': 'uz',
        'category_slug': 'sertifikatsiya',
        'category_name': 'Sertifikatsiya',
        'category_icon': '🏅',
        'is_featured': True,
        'read_time': 8,
        'cover_image': 'https://images.unsplash.com/photo-1450101499163-c8848c66ca85?w=1200&q=80',
        'title': 'ISO 9001:2015 Sertifikatsiyasini Olish: To\'liq Amaliy Qo\'llanma',
        'excerpt': 'ISO 9001:2015 — dunyodagi eng keng tarqalgan sifat menejmenti standarti. Ushbu qo\'llanmada O\'zbekiston korxonalari uchun sertifikatni qanday olish, qancha vaqt va mablag\' ketishi batafsil ko\'rsatilgan.',
        'content': '''ISO 9001:2015 — Sifat Menejmenti Tizimi (SMT) bo'yicha xalqaro standart bo'lib, Xalqaro Standartlashtirish Tashkiloti (ISO) tomonidan nashr etiladi. Bugungi kunda dunyoning 170+ mamlakatida 1 milliondan ortiq tashkilot ushbu sertifikatga ega (manba: ISO Survey of Certifications 2023, iso.org).

## ISO 9001:2015 Nima?

ISO 9001 standarti sifat menejmentining 7 ta asosiy printsipiga asoslanadi:
- **Mijozga yo'nalganlik** — mijoz ehtiyojlarini tushunish va ularni qondirish
- **Yetakchilik** — rahbariyatning sifatga intilishi
- **Xodimlarning ish faolligi** — barcha bo'g'inlarning jarayonga jalb etilishi
- **Jarayon yondashuvi** — izchil natijalarga erishish
- **Yaxshilanish** — uzluksiz takomillashtirish madaniyati
- **Dalillarga asoslangan qarorlar** — tahlil va baholashga tayanish
- **Munosabatlarni boshqarish** — etkazib beruvchilar bilan hamkorlik

*Manba: ISO 9001:2015 §0.2 "Quality management principles", International Organization for Standardization, Geneva.*

## O'zbekistonda ISO 9001 Holati

O'zbekiston Standartlashtirish, Metrologiya va Sertifikatsiya Agentligi (UzDST) ISO 9001 ni O'zR DST ISO 9001:2015 sifatida tasdiqlagan. Sertifikat olish uchun O'zbekistonda faoliyat yurituvchi akkreditatsiya qilingan organ murojaat qilish mumkin:

- **UzDST akkreditatsiya markazi** — standart.uz
- Xalqaro organlar: Bureau Veritas, SGS, TÜV SÜD, Intertek (barchasi O'zbekistonda vakolatxonaga ega)

*Manba: UzDST rasmiy sayti, standart.uz/accreditation*

## Sertifikatsiya Bosqichlari

### 1-bosqich: Tayyorgarlik (1–3 oy)

**Gap-tahlil o'tkazish.** Joriy jarayonlaringizni ISO 9001 talablari bilan solishtirasiz. Bu bosqich standart §4-10 bo'limlariga muvofiqligini aniqlaydi.

**Sifat menejmenti tizimini joriy qilish:**
- Sifat siyosati va maqsadlarini belgilash (ISO 9001 §5.2, §6.2)
- Jarayonlar xaritasini tuzish
- Majburiy hujjatlarni tayyorlash (9 ta majburiy yozuv)

### 2-bosqich: Ichki audit (1–2 oy)

ISO 9001 §9.2 talabiga binoan tashkilot ichki audit o'tkazishi shart. Audit tekshiradi:
- Hujjatlashtirilgan axborot to'liqligi
- Jarayonlarning amalda ishlashi
- Manba: ISO 19011:2018 "Guidelines for auditing management systems"

### 3-bosqich: Rahbariyat ko'rib chiqishi

ISO 9001 §9.3 bo'yicha rahbariyat yiliga kamida bir marta SMTni ko'rib chiqishi va qarorlar qabul qilishi kerak.

### 4-bosqich: Sertifikatsiya auditi (2 bosqich)

**1-bosqich (hujjatli audit):** Auditor tashkilotingiz hujjatlarini tekshiradi — 1–2 kun.

**2-bosqich (sahadagi audit):** Auditor korxonada ishlarni kuzatadi, xodimlar bilan suhbatlashadi — 2–5 kun (tashkilot hajmiga qarab).

### 5-bosqich: Sertifikat berish

Muvofiqliklar aniqlansa, akkreditatsiya organi **3 yillik sertifikat** beradi. Har yili kuzatuv auditi o'tkaziladi.

## Vaqt va Xarajatlar

| Bosqich | Vaqt | Taxminiy xarajat |
|---------|------|-----------------|
| Tayyorgarlik va joriy qilish | 2–4 oy | Maslahat: $1,500–$5,000 |
| Sertifikatsiya auditi | 1–2 oy | $1,200–$3,500 |
| Yillik kuzatuv | 1 oy/yil | $800–$1,500 |

*Eslatma: narxlar tashkilot hajmi (xodimlar soni, jarayonlar murakkabligi) va akkreditatsiya organiga qarab farq qiladi.*

## Sertifikatning Foydasi

Xalqaro Savdo Markazi (ITC, intracen.org) ma'lumotlariga ko'ra, ISO 9001 sertifikatiga ega bo'lgan kichik va o'rta korxonalar:
- Eksport imkoniyatlarini **40-60% ko'paytiradi**
- Mijozlar reklamatsiyalarini **25-35% kamaytiradi**
- Jarayon samaradorligini **20-30% oshiradi**

O'zbekistonda davlat xaridlari tenderlarida va yirik korporatsiyalar bilan shartnoma tuzishda ISO 9001 sertifikati tobora keng talab qilinmoqda.

## Standart Talablari (§4-10 qisqacha)

**§4 — Tashkilot konteksti:** Ichki va tashqi masalalar, manfaatdor tomonlar tahlili.

**§5 — Yetakchilik:** Rahbariyat majburiyatlari, sifat siyosati, rollar va mas'uliyat.

**§6 — Rejalashtirish:** Xatarlar va imkoniyatlarni aniqlash, sifat maqsadlari.

**§7 — Qo'llab-quvvatlash:** Resurslar, kompetentlik, xabardorlik, aloqa, hujjatlashtirilgan axborot.

**§8 — Faoliyat:** Mahsulot/xizmat rejalashtirish, dizayn, nazorat va chiqarib yuborish.

**§9 — Ishlash baholash:** Monitoring, o'lchash, tahlil, ichki audit, rahbariyat ko'rib chiqishi.

**§10 — Yaxshilanish:** Nomuvofiqliklar, tuzatuvchi choralar, uzluksiz takomillashtirish.

## Xulosa

ISO 9001:2015 — bu nafaqat sertifikat, balki korxonangizni tizimli va raqobatbardosh boshqarish yo'lidir. O'zbekiston iqtisodiyotining global bozorga integratsiyalashuvi davom etar ekan, ushbu standart korxonalar uchun eksport va sheriklik imkoniyatlarini ochishning eng ishonchli usuli bo'lib qoladi.

---

*Manbalar: ISO.org — "ISO 9001:2015 Quality management systems – Requirements"; UzDST — standart.uz; ITC — "Quality for Export" (intracen.org); ISO Survey of Certifications 2023.*''',
    },

    # ─────────────────────────────────────────────────────────────
    # ARTICLE 1 — ISO 9001:2015  (RU)
    # ─────────────────────────────────────────────────────────────
    {
        'slug': 'iso-9001-2015-sertifikatsiya-qollanma-ru',
        'group_key': 'iso-9001-2015-certification-guide',
        'language': 'ru',
        'category_slug': 'sertifikatsiya',
        'category_name': 'Сертификация',
        'category_icon': '🏅',
        'is_featured': True,
        'read_time': 8,
        'cover_image': 'https://images.unsplash.com/photo-1450101499163-c8848c66ca85?w=1200&q=80',
        'title': 'Получение сертификата ISO 9001:2015: Полное практическое руководство',
        'excerpt': 'ISO 9001:2015 — самый распространённый стандарт системы менеджмента качества в мире. В этом руководстве подробно описан процесс получения сертификата для предприятий Узбекистана, сроки и стоимость.',
        'content': '''ISO 9001:2015 — международный стандарт системы менеджмента качества (СМК), издаваемый Международной организацией по стандартизации (ISO). По данным ISO Survey of Certifications 2023 (iso.org), более 1 миллиона организаций в 170+ странах имеют этот сертификат.

## Что такое ISO 9001:2015?

Стандарт основан на 7 принципах менеджмента качества:
- **Ориентация на потребителя** — понимание и удовлетворение потребностей клиентов
- **Лидерство** — приверженность руководства качеству
- **Вовлечённость персонала** — участие всех сотрудников
- **Процессный подход** — достижение стабильных результатов
- **Улучшение** — культура непрерывного совершенствования
- **Решения на основе фактов** — анализ данных и оценка
- **Менеджмент взаимоотношений** — партнёрство с поставщиками

*Источник: ISO 9001:2015 §0.2 "Quality management principles", International Organization for Standardization, Geneva.*

## ISO 9001 в Узбекистане

Агентство по стандартизации, метрологии и сертификации Узбекистана (UzDST) утвердило стандарт как O'zR DST ISO 9001:2015. Для получения сертификата можно обратиться к аккредитованным органам:

- **Аккредитационный центр UzDST** — standart.uz
- Международные органы: Bureau Veritas, SGS, TÜV SÜD, Intertek (все имеют представительства в Узбекистане)

*Источник: Официальный сайт UzDST, standart.uz/accreditation*

## Этапы сертификации

### Этап 1: Подготовка (1–3 месяца)

**Анализ разрывов (Gap Analysis).** Сравниваете текущие процессы с требованиями ISO 9001, разделы §4–10.

**Внедрение системы менеджмента качества:**
- Разработка политики и целей в области качества (ISO 9001 §5.2, §6.2)
- Составление карты процессов
- Подготовка обязательной документации (9 обязательных записей)

### Этап 2: Внутренний аудит (1–2 месяца)

Согласно требованию ISO 9001 §9.2 организация обязана проводить внутренние аудиты. Аудит проверяет:
- Полноту документированной информации
- Фактическое функционирование процессов
- Источник: ISO 19011:2018 "Руководящие указания по аудиту систем менеджмента"

### Этап 3: Анализ со стороны руководства

По ISO 9001 §9.3 руководство обязано не реже одного раза в год анализировать СМК.

### Этап 4: Сертификационный аудит (2 стадии)

**Стадия 1 (документарный аудит):** Аудитор проверяет документацию — 1–2 дня.

**Стадия 2 (аудит на месте):** Аудитор наблюдает за работой, беседует с сотрудниками — 2–5 дней.

### Этап 5: Выдача сертификата

При подтверждении соответствия орган по сертификации выдаёт **сертификат сроком на 3 года**. Ежегодно проводятся надзорные аудиты.

## Сроки и стоимость

| Этап | Срок | Ориентировочная стоимость |
|------|------|--------------------------|
| Подготовка и внедрение | 2–4 мес. | Консалтинг: $1 500–$5 000 |
| Сертификационный аудит | 1–2 мес. | $1 200–$3 500 |
| Ежегодный надзор | 1 мес./год | $800–$1 500 |

*Цены зависят от размера организации и выбранного органа по сертификации.*

## Преимущества сертификата

По данным Международного торгового центра (ITC, intracen.org), МСП с сертификатом ISO 9001:
- Увеличивают экспортные возможности на **40–60%**
- Снижают количество рекламаций на **25–35%**
- Повышают эффективность процессов на **20–30%**

В Узбекистане наличие ISO 9001 становится всё более обязательным условием в государственных тендерах и контрактах с крупными корпорациями.

## Требования стандарта (§4–10 кратко)

**§4 — Среда организации:** Анализ внутренних и внешних факторов, заинтересованные стороны.

**§5 — Лидерство:** Обязательства руководства, политика в области качества, роли и ответственность.

**§6 — Планирование:** Риски и возможности, цели в области качества.

**§7 — Обеспечение:** Ресурсы, компетентность, осведомлённость, коммуникация, документированная информация.

**§8 — Деятельность:** Планирование продукции/услуг, проектирование, управление, выпуск.

**§9 — Оценка результативности:** Мониторинг, измерение, анализ, внутренний аудит, анализ руководством.

**§10 — Улучшение:** Несоответствия, корректирующие действия, непрерывное улучшение.

## Заключение

ISO 9001:2015 — это не просто сертификат, а системный подход к управлению предприятием. По мере интеграции экономики Узбекистана в глобальные рынки этот стандарт остаётся надёжным способом открыть новые экспортные и партнёрские возможности.

---

*Источники: ISO.org — "ISO 9001:2015 Quality management systems – Requirements"; UzDST — standart.uz; ITC — "Quality for Export" (intracen.org); ISO Survey of Certifications 2023.*''',
    },

    # ─────────────────────────────────────────────────────────────
    # ARTICLE 1 — ISO 9001:2015  (EN)
    # ─────────────────────────────────────────────────────────────
    {
        'slug': 'iso-9001-2015-certification-guide-en',
        'group_key': 'iso-9001-2015-certification-guide',
        'language': 'en',
        'category_slug': 'sertifikatsiya',
        'category_name': 'Certification',
        'category_icon': '🏅',
        'is_featured': True,
        'read_time': 8,
        'cover_image': 'https://images.unsplash.com/photo-1450101499163-c8848c66ca85?w=1200&q=80',
        'title': 'Getting ISO 9001:2015 Certified: A Complete Practical Guide',
        'excerpt': 'ISO 9001:2015 is the world\'s most widely adopted quality management standard. This guide walks Uzbekistan businesses through the entire certification process, timeline, and costs.',
        'content': '''ISO 9001:2015 is the international standard for Quality Management Systems (QMS), published by the International Organization for Standardization (ISO). According to the ISO Survey of Certifications 2023 (iso.org), more than 1 million organizations across 170+ countries hold this certification.

## What Is ISO 9001:2015?

The standard is built on 7 quality management principles:
- **Customer focus** — understanding and satisfying customer needs
- **Leadership** — top management commitment to quality
- **Engagement of people** — involving all levels of the organization
- **Process approach** — achieving consistent, predictable results
- **Improvement** — culture of continual enhancement
- **Evidence-based decision making** — analysis and evaluation grounding decisions
- **Relationship management** — mutually beneficial supplier partnerships

*Source: ISO 9001:2015 §0.2 "Quality management principles", International Organization for Standardization, Geneva.*

## ISO 9001 in Uzbekistan

The Uzbekistan Agency for Technical Regulation (UzDST) has adopted the standard as O'zR DST ISO 9001:2015. Certification bodies active in Uzbekistan include:

- **UzDST Accreditation Centre** — standart.uz
- International bodies: Bureau Veritas, SGS, TÜV SÜD, Intertek (all with local presence)

*Source: UzDST official website, standart.uz/accreditation*

## Certification Steps

### Step 1: Gap Analysis & Preparation (1–3 months)

**Conduct a gap analysis.** Compare your current processes against ISO 9001 requirements (clauses §4–10) to identify what needs to change.

**Implement the QMS:**
- Define quality policy and objectives (ISO 9001 §5.2, §6.2)
- Map key processes
- Prepare 9 mandatory documented records

### Step 2: Internal Audit (1–2 months)

ISO 9001 §9.2 requires the organization to conduct internal audits to verify:
- Completeness of documented information
- Actual operation of processes
- Reference: ISO 19011:2018 "Guidelines for auditing management systems"

### Step 3: Management Review

Per ISO 9001 §9.3, top management must review the QMS at least once per year and make decisions on needed changes.

### Step 4: Certification Audit (2 stages)

**Stage 1 (Document review):** Auditor reviews your documentation remotely or on-site — 1–2 days.

**Stage 2 (On-site audit):** Auditor observes operations, interviews staff — 2–5 days depending on company size.

### Step 5: Certificate Issued

If conformity is confirmed, the certification body issues a **3-year certificate**. Annual surveillance audits maintain validity.

## Timeline and Costs

| Stage | Duration | Estimated Cost |
|-------|----------|----------------|
| Preparation & implementation | 2–4 months | Consulting: $1,500–$5,000 |
| Certification audit | 1–2 months | $1,200–$3,500 |
| Annual surveillance | 1 month/year | $800–$1,500 |

*Costs vary based on organization size and chosen certification body.*

## Benefits of Certification

According to the International Trade Centre (ITC, intracen.org), SMEs certified to ISO 9001:
- **Increase export opportunities by 40–60%**
- **Reduce customer complaints by 25–35%**
- **Improve process efficiency by 20–30%**

In Uzbekistan, ISO 9001 is increasingly required in government procurement tenders and contracts with major corporations.

## Standard Requirements Summary (§4–10)

**§4 — Context of the organization:** Internal/external issues, interested parties analysis.

**§5 — Leadership:** Management commitments, quality policy, roles and responsibilities.

**§6 — Planning:** Risks and opportunities, quality objectives.

**§7 — Support:** Resources, competence, awareness, communication, documented information.

**§8 — Operation:** Product/service planning, design, control, release.

**§9 — Performance evaluation:** Monitoring, measurement, analysis, internal audit, management review.

**§10 — Improvement:** Nonconformities, corrective actions, continual improvement.

## Conclusion

ISO 9001:2015 is not just a certificate — it is a systematic approach to running your business. As Uzbekistan's economy continues integrating into global markets, this standard remains the most reliable pathway to unlock new export and partnership opportunities.

---

*Sources: ISO.org — "ISO 9001:2015 Quality management systems – Requirements"; UzDST — standart.uz; ITC — "Quality for Export" (intracen.org); ISO Survey of Certifications 2023.*''',
    },

    # ─────────────────────────────────────────────────────────────
    # ARTICLE 2 — CE Marking  (UZ)
    # ─────────────────────────────────────────────────────────────
    {
        'slug': 'ce-belgisi-yevropa-bozori-uzbekiston-uz',
        'group_key': 'ce-marking-european-market-guide',
        'language': 'uz',
        'category_slug': 'eksport',
        'category_name': 'Eksport',
        'category_icon': '🌍',
        'is_featured': False,
        'read_time': 7,
        'cover_image': 'https://images.unsplash.com/photo-1521737852567-6949f3f9f2b5?w=1200&q=80',
        'title': 'CE Belgisi: O\'zbekiston Tovarlarini Yevropa Bozorlariga Chiqarish Qo\'llanmasi',
        'excerpt': 'CE belgisi — Yevropa Ittifoqi bozorlarida savdo qilish uchun majburiy talabdir. Ushbu maqolada O\'zbekiston ishlab chiqaruvchilari uchun CE belgisini olish jarayoni, talab qilinadigan hujjatlar va xarajatlar batafsil tushuntirilgan.',
        'content': '''CE belgisi (fransuzcha "Conformité Européenne" — Yevropa muvofiqlik) — Yevropa Ittifoqi (YeI) bozorida mahsulotni erkin sotish huquqini beruvchi belgi. Yevropa Komissiyasining "Blue Guide 2022" hujjatiga ko'ra, CE belgisi ishlab chiqaruvchining mahsulot YeI direktivalari va texnik reglamentlariga muvofiqligi haqidagi deklaratsiyasidir.

*Manba: European Commission, "The 'Blue Guide' on the implementation of EU product rules 2022", publications.europa.eu*

## CE Belgisi Nima Uchun Kerak?

CE belgisi olmagan mahsulotni YeI mamlakatlarida (27 ta davlat + Islandiya, Liechtenstein, Norvegiya — EEA) qonuniy ravishda sotib bo'lmaydi. Bu siz uchun nima degani:

- 450+ million aholisi bo'lgan YeI bozorida raqobat qilish imkoniyati
- Yevropa importyorlari va chakana sotuvchilar bilan ishlash imkoniyati
- O'zbekistonda ishlab chiqarilgan mahsulotlarning xalqaro raqobatbardoshligini oshirish

## Qaysi Mahsulotlarga CE Belgisi Kerak?

Barcha mahsulotlarga emas — faqat muayyan direktivalar doirasiga kiruvchi mahsulot guruhlariga:

| Mahsulot turi | Asosiy direktiva |
|--------------|-----------------|
| Elektr jihozlari | LVD 2014/35/EU |
| Elektronika (EMC) | EMC Directive 2014/30/EU |
| Mashinalar, uskunalar | Machinery Directive 2006/42/EC |
| O'yinchoqlar | Toy Safety 2009/48/EC |
| Tibbiy asboblar | MDR 2017/745 |
| Shaxsiy himoya vositalari | PPE Regulation 2016/425 |
| Qurilish materiallari | CPR 305/2011/EU |
| Radio uskunalari | RED 2014/53/EU |

*Manba: Yevropa Komissiyasi — ec.europa.eu/growth/single-market/ce-marking*

## CE Belgisini Olish Bosqichlari

### 1-bosqich: Mahsulot uchun tegishli direktiva(lar)ni aniqlash

Mahsulotingizga qaysi YeI direktivasi yoki reglamenti taqdim etilishini aniqlashtirish uchun Yevropa Komissiyasining rasmiy bazasidan foydalanasiz: eur-lex.europa.eu

### 2-bosqich: Muvofiqlashtirilgan standartlar bo'yicha sinovlar

YeI Official Journal'da nashr etilgan muvofiqlashtirilgan standartlar (harmonized standards) ro'yxatiga kiruvchi standartlarga muvofiqlik — CE belgilashning texnik asosi. Masalan, elektr jihozlari uchun EN 60950, elektronika uchun EN 55032.

**Sinov qayerda o'tkaziladi?**
- YeI akkreditatsiya tizimiga (EA, ILAC) kiruvchi sinov laboratoriyalari
- O'zbekistonda: O'zDST sinov laboratoriyalari, xalqaro organlarning Toshkent vakolatxonalari

### 3-bosqich: Texnik fayl (Technical File) tuzish

Texnik fayl quyidagilarni o'z ichiga oladi (Blue Guide 2022, §4.3):
- Mahsulot tavsifi va rasmlar/chizmalar
- Muvofiqlashtirilgan standartlar ro'yxati
- Sinov hisobotlari va hisob-kitoblar
- Xatarlarni baholash natijasi
- Foydalanish bo'yicha yo'riqnoma (o'quvchi tilida)

Texnik fayl kamida **10 yil** saqlanishi shart.

### 4-bosqich: EU Muvofiqlik Deklaratsiyasi (DoC)

Ishlab chiqaruvchi (yoki YeI doirasidagi vakolatli vakil) **EU Declaration of Conformity (DoC)** ni imzolaydi. Ushbu hujjat quyidagilarni o'z ichiga oladi:
- Ishlab chiqaruvchi nomi va manzili
- Mahsulot tavsifi va identifikatsiyasi
- Tegishli YeI direktivalari ro'yxati
- Tegishli standartlar ro'yxati
- Mas'ul shaxsning imzosi va sanasi

*Manba: EU Regulation 765/2008, Article 30*

### 5-bosqich: Mahsulotga CE belgisini joylashtirish

DoC imzolangach, mahsulotga CE belgisi qo'yiladi. Belgi aniq va o'chirib bo'lmaydigan tarzda joylashtirilishi kerak. Belgi o'lchami: kichigi 5 mm (Yevropa Komissiyasi rasm standartlari).

## Notified Body (Belgilangan Organ) Qachon Kerak?

Yuqori xavfli mahsulotlar uchun (mashinalar, tibbiy asboblar) mustaqil tekshiruv Notified Body tomonidan o'tkazilishi shart. Notified Body tizimi EC rasmiy bazasida: ec.europa.eu/growth/tools-databases/nando

O'zbekiston ishlab chiqaruvchilari uchun eng qulay Notified Bodylar: Bureau Veritas, SGS, TÜV Rheinland.

## Vaqt va Xarajatlar

| Bosqich | Vaqt | Taxminiy xarajat |
|---------|------|-----------------|
| Texnik tahlil va direktiva aniqlash | 2–4 hafta | $500–$1,500 |
| Sinovlar (laboratoriya) | 4–12 hafta | $2,000–$15,000 |
| Texnik fayl tayyorlash | 2–6 hafta | $1,000–$3,000 |
| Notified Body (agar kerak) | 2–6 oy | $5,000–$20,000+ |

*Eslatma: Xarajatlar mahsulot turiga va murakkabligiga qarab sezilarli farq qiladi.*

## O'zbekiston Uchun Amaliy Maslahatlar

**YeI vakolatli vakili (Authorised Representative):** YeI doirasida ro'yxatdan o'tmagan O'zbekiston kompaniyalari uchun YeI a'zosi mamlakatda vakolatli vakil tayinlash tavsiya etiladi. Vakil hujjatlar va xavfsizlik ma'lumotlar bilan bog'liq javobgarliklarni oladi.

**Yevropa importyori bilan hamkorlik:** Ko'pincha YeI importyori CE jarayonini o'z zimmasiga oladi va xarajatlarga hissa qo'shadi — bu kichik O'zbekiston eksportchilari uchun qulay yo'l.

**Standartlar bazasi:** Barcha muvofiqlashtirilgan standartlar bepul ko'rish uchun: ec.europa.eu/growth/single-market/european-standards

## Xulosa

CE belgisi — O'zbekiston ishlab chiqaruvchilari uchun 450 millionlik YeI bozorini ochuvchi kalit. Jarayon murakkabroq ko'rinsa ham, to'g'ri tayyorgarlik va malakali maslahat bilan 3–6 oy ichida erishish mumkin.

---

*Manbalar: European Commission — "The 'Blue Guide' on the implementation of EU product rules 2022" (publications.europa.eu); CE Marking official portal (ec.europa.eu/growth/single-market/ce-marking); EU Regulation 765/2008; ITC — "Standards and quality infrastructure" (intracen.org).*''',
    },

    # ─────────────────────────────────────────────────────────────
    # ARTICLE 2 — CE Marking  (RU)
    # ─────────────────────────────────────────────────────────────
    {
        'slug': 'ce-markirovka-evropeyskiy-rynok-ru',
        'group_key': 'ce-marking-european-market-guide',
        'language': 'ru',
        'category_slug': 'eksport',
        'category_name': 'Экспорт',
        'category_icon': '🌍',
        'is_featured': False,
        'read_time': 7,
        'cover_image': 'https://images.unsplash.com/photo-1521737852567-6949f3f9f2b5?w=1200&q=80',
        'title': 'Знак CE: Руководство по выходу товаров из Узбекистана на рынок ЕС',
        'excerpt': 'Знак CE является обязательным требованием для торговли на рынках Европейского союза. В этой статье подробно описан процесс получения CE для производителей из Узбекистана, необходимая документация и затраты.',
        'content': '''Знак CE (от французского «Conformité Européenne» — европейское соответствие) — маркировка, дающая право на свободную продажу товаров на рынке Европейского союза. Согласно «Синему руководству 2022» Европейской комиссии, знак CE является декларацией производителя о соответствии продукции директивам и техническим регламентам ЕС.

*Источник: European Commission, "The 'Blue Guide' on the implementation of EU product rules 2022", publications.europa.eu*

## Зачем нужен знак CE?

Без знака CE продавать продукцию на территории государств ЕС (27 стран + Исландия, Лихтенштейн, Норвегия — ЕЭЗ) законодательно запрещено. Это означает:

- Доступ к рынку с населением более 450 миллионов человек
- Возможность работы с европейскими импортёрами и ритейлерами
- Повышение международной конкурентоспособности продукции из Узбекистана

## Каким товарам нужен знак CE?

Не всем — только продуктовым группам, охватываемым соответствующими директивами:

| Вид продукции | Основная директива |
|--------------|-------------------|
| Электрооборудование | LVD 2014/35/EU |
| Электроника (ЭМС) | EMC Directive 2014/30/EU |
| Машины и оборудование | Machinery Directive 2006/42/EC |
| Игрушки | Toy Safety 2009/48/EC |
| Медицинские изделия | MDR 2017/745 |
| СИЗ | PPE Regulation 2016/425 |
| Строительные материалы | CPR 305/2011/EU |
| Радиооборудование | RED 2014/53/EU |

*Источник: Европейская комиссия — ec.europa.eu/growth/single-market/ce-marking*

## Этапы получения знака CE

### Этап 1: Определение применимых директив

Для уточнения применимых директив используйте официальную базу ЕС: eur-lex.europa.eu

### Этап 2: Испытания на соответствие гармонизированным стандартам

Гармонизированные стандарты, опубликованные в Official Journal ЕС, составляют техническую основу CE-маркировки. Например, для электрооборудования — EN 60950, для электроники — EN 55032.

**Где проводятся испытания?**
- Аккредитованные лаборатории системы EA / ILAC
- В Узбекистане: испытательные лаборатории UzDST, представительства международных органов в Ташкенте

### Этап 3: Составление технического файла (Technical File)

Технический файл включает (Blue Guide 2022, §4.3):
- Описание изделия, чертежи/схемы
- Перечень применённых гармонизированных стандартов
- Протоколы испытаний и расчёты
- Оценку рисков
- Инструкцию по применению на языке конечного пользователя

Технический файл должен храниться не менее **10 лет**.

### Этап 4: Декларация о соответствии ЕС (DoC)

Производитель (или уполномоченный представитель в ЕС) подписывает **EU Declaration of Conformity (DoC)**, которая содержит:
- Наименование и адрес производителя
- Описание и идентификацию продукта
- Перечень применимых директив ЕС
- Перечень применённых стандартов
- Подпись ответственного лица с датой

*Источник: Регламент ЕС 765/2008, Статья 30*

### Этап 5: Нанесение знака CE

После подписания DoC знак CE наносится на продукт — чётко и несмываемо. Минимальный размер знака: 5 мм (стандарты изображения Европейской комиссии).

## Когда нужен Notified Body?

Для продукции высокого риска (машины, медицинские изделия) обязательна независимая проверка Notified Body (уполномоченным органом). База данных уполномоченных органов ЕС: ec.europa.eu/growth/tools-databases/nando

Для производителей из Узбекистана наиболее удобны: Bureau Veritas, SGS, TÜV Rheinland.

## Сроки и стоимость

| Этап | Срок | Ориентировочные затраты |
|------|------|------------------------|
| Технический анализ и определение директив | 2–4 нед. | $500–$1 500 |
| Испытания в лаборатории | 4–12 нед. | $2 000–$15 000 |
| Подготовка технического файла | 2–6 нед. | $1 000–$3 000 |
| Notified Body (при необходимости) | 2–6 мес. | $5 000–$20 000+ |

*Затраты существенно варьируются в зависимости от типа и сложности продукции.*

## Практические советы для Узбекистана

**Уполномоченный представитель в ЕС (Authorised Representative):** Для компаний из Узбекистана, не имеющих юридического адреса в ЕС, рекомендуется назначить уполномоченного представителя в одной из стран ЕС, который принимает на себя ответственность за документацию и данные по безопасности.

**Партнёрство с европейским импортёром:** Нередко импортёр из ЕС берёт на себя процесс CE-маркировки и участвует в расходах — это удобный путь для небольших узбекских экспортёров.

**База стандартов:** Все гармонизированные стандарты в открытом доступе: ec.europa.eu/growth/single-market/european-standards

## Заключение

Знак CE — это ключ к рынку ЕС с аудиторией 450+ миллионов потребителей для производителей из Узбекистана. Несмотря на кажущуюся сложность, при правильной подготовке и профессиональной консультации этого можно достичь за 3–6 месяцев.

---

*Источники: Европейская комиссия — «Синее руководство по применению норм ЕС для продуктов 2022» (publications.europa.eu); Официальный портал CE-маркировки (ec.europa.eu); Регламент ЕС 765/2008; ITC — "Standards and quality infrastructure" (intracen.org).*''',
    },

    # ─────────────────────────────────────────────────────────────
    # ARTICLE 2 — CE Marking  (EN)
    # ─────────────────────────────────────────────────────────────
    {
        'slug': 'ce-marking-european-market-uzbekistan-en',
        'group_key': 'ce-marking-european-market-guide',
        'language': 'en',
        'category_slug': 'eksport',
        'category_name': 'Export',
        'category_icon': '🌍',
        'is_featured': False,
        'read_time': 7,
        'cover_image': 'https://images.unsplash.com/photo-1521737852567-6949f3f9f2b5?w=1200&q=80',
        'title': 'CE Marking: A Guide for Uzbekistan Manufacturers Entering the EU Market',
        'excerpt': 'CE marking is a mandatory requirement for selling products in European Union markets. This article walks Uzbekistan manufacturers through the full CE process, required documentation, and costs.',
        'content': '''CE marking (from French "Conformité Européenne" — European conformity) is the mark that gives manufacturers the right to sell products freely on the European Union single market. According to the European Commission's "Blue Guide 2022", CE marking is the manufacturer's declaration that the product complies with all applicable EU directives and technical regulations.

*Source: European Commission, "The 'Blue Guide' on the implementation of EU product rules 2022", publications.europa.eu*

## Why Do You Need CE Marking?

Without CE marking, it is legally prohibited to sell products in EU member states (27 countries + Iceland, Liechtenstein, Norway — the EEA). For Uzbekistan manufacturers, this means:

- Access to a market of 450+ million consumers
- Ability to work with European importers and retailers
- Enhanced international competitiveness of products made in Uzbekistan

## Which Products Require CE Marking?

Not all products — only those covered by specific EU directives:

| Product type | Key directive |
|-------------|--------------|
| Electrical equipment | LVD 2014/35/EU |
| Electronics (EMC) | EMC Directive 2014/30/EU |
| Machinery & equipment | Machinery Directive 2006/42/EC |
| Toys | Toy Safety 2009/48/EC |
| Medical devices | MDR 2017/745 |
| Personal protective equipment | PPE Regulation 2016/425 |
| Construction products | CPR 305/2011/EU |
| Radio equipment | RED 2014/53/EU |

*Source: European Commission — ec.europa.eu/growth/single-market/ce-marking*

## CE Marking Steps

### Step 1: Identify Applicable Directives

Use the official EU legislation database to identify which directive(s) apply to your product: eur-lex.europa.eu

### Step 2: Testing Against Harmonised Standards

Harmonised standards published in the EU Official Journal form the technical basis for CE marking. For example, EN 60950 for low-voltage electrical equipment, EN 55032 for electronics EMC.

**Where to test:**
- Laboratories accredited under the EA / ILAC system
- In Uzbekistan: UzDST testing laboratories, Tashkent offices of international certification bodies

### Step 3: Compile the Technical File

The Technical File must include (Blue Guide 2022, §4.3):
- Product description, drawings and diagrams
- List of harmonised standards applied
- Test reports and calculations
- Risk assessment results
- Instructions for use in the language of the end user

The Technical File must be retained for at least **10 years**.

### Step 4: EU Declaration of Conformity (DoC)

The manufacturer (or an authorised representative established in the EU) signs the **EU Declaration of Conformity (DoC)**, which must include:
- Manufacturer name and address
- Product description and identification
- List of applicable EU directives
- List of harmonised standards applied
- Signature of the responsible person with date

*Source: EU Regulation 765/2008, Article 30*

### Step 5: Affix the CE Mark

Once the DoC is signed, the CE mark is affixed to the product — clearly and indelibly. Minimum mark size: 5 mm (European Commission graphical standards).

## When Is a Notified Body Required?

For high-risk products (machinery, medical devices) an independent assessment by a Notified Body is mandatory. The EU Notified Body database: ec.europa.eu/growth/tools-databases/nando

The most accessible Notified Bodies for Uzbekistan manufacturers: Bureau Veritas, SGS, TÜV Rheinland.

## Timeline and Costs

| Stage | Duration | Estimated Cost |
|-------|----------|----------------|
| Technical analysis and directive identification | 2–4 weeks | $500–$1,500 |
| Laboratory testing | 4–12 weeks | $2,000–$15,000 |
| Technical File preparation | 2–6 weeks | $1,000–$3,000 |
| Notified Body (if required) | 2–6 months | $5,000–$20,000+ |

*Costs vary significantly depending on product type and complexity.*

## Practical Tips for Uzbekistan Exporters

**EU Authorised Representative:** Uzbekistan companies without a legal address in the EU should appoint an Authorised Representative in an EU member state, who takes on responsibility for documentation and safety data obligations.

**Partner with a European Importer:** Many EU importers are willing to manage the CE process and share costs — an efficient route for smaller Uzbekistan exporters.

**Standards Database:** All harmonised standards are publicly searchable: ec.europa.eu/growth/single-market/european-standards

## Conclusion

CE marking is the key that unlocks the 450+ million consumer EU market for Uzbekistan manufacturers. While the process may appear complex, with proper preparation and expert guidance it is achievable within 3–6 months.

---

*Sources: European Commission — "The 'Blue Guide' on the implementation of EU product rules 2022" (publications.europa.eu); CE Marking official portal (ec.europa.eu); EU Regulation 765/2008; ITC — "Standards and quality infrastructure" (intracen.org).*''',
    },
]


class Command(BaseCommand):
    help = 'Rasmiy manbalar asosida 2 ta blog maqolasini (har biri 3 tilda) yuklaydi'

    def handle(self, *args, **options):
        created_count = 0
        for data in POSTS:
            # Kategoriya topish yoki yaratish
            cat, _ = Category.objects.get_or_create(
                slug=data['category_slug'],
                defaults={
                    'name': data['category_name'],
                    'icon': data['category_icon'],
                },
            )

            post, created = BlogPost.objects.get_or_create(
                slug=data['slug'],
                defaults={
                    'title': data['title'],
                    'excerpt': data['excerpt'],
                    'content': data['content'],
                    'category': cat,
                    'cover_image': data['cover_image'],
                    'language': data['language'],
                    'group_key': data.get('group_key', ''),
                    'is_published': True,
                    'is_featured': data['is_featured'],
                    'read_time': data['read_time'],
                },
            )

            if not created:
                # Mavjud postga group_key ni yangilash (eski deploy uchun)
                if post.group_key != data.get('group_key', ''):
                    BlogPost.objects.filter(pk=post.pk).update(group_key=data.get('group_key', ''))
                self.stdout.write(f'  [=] (mavjud) {data["slug"]}')
            else:
                created_count += 1
                self.stdout.write(self.style.SUCCESS(f'  [+] {data["language"].upper()}: {data["title"][:60]}'))

        self.stdout.write(self.style.SUCCESS(
            f'\nBlog maqolalari: {created_count} yangi yaratildi, {len(POSTS) - created_count} allaqachon mavjud.'
        ))
