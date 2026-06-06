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

    # ─────────────────────────────────────────────────────────────
    # ARTICLE 3 — ISO 14001:2015 Environmental Management  (UZ)
    # ─────────────────────────────────────────────────────────────
    {
        'slug': 'iso-14001-2015-atrof-muhit-uz',
        'group_key': 'iso-14001-2015-env-management',
        'language': 'uz',
        'category_slug': 'sertifikatsiya',
        'category_name': 'Sertifikatsiya',
        'category_icon': '🏅',
        'is_featured': False,
        'read_time': 7,
        'cover_image': 'https://images.unsplash.com/photo-1441974231531-c6227db76b6e?w=1200&q=80',
        'title': 'ISO 14001:2015 Atrof-Muhit Menejmenti: O\'zbekiston Korxonalari Uchun Qo\'llanma',
        'excerpt': 'ISO 14001:2015 — atrof-muhitni boshqarish tizimining xalqaro standarti. Ushbu maqolada O\'zbekiston korxonalari uchun sertifikat olish bosqichlari, UzDST talablari va xarajatlar batafsil yoritilgan.',
        'content': '''ISO 14001:2015 — Atrof-muhit menejmenti tizimi (AMT) bo'yicha xalqaro standart bo'lib, ISO tomonidan nashr etiladi. ISO Survey 2023 ma'lumotlariga ko'ra, dunyoning 180+ mamlakatida 400 000 dan ortiq tashkilot ushbu sertifikatga ega (manba: iso.org).

## ISO 14001:2015 Nima?

ISO 14001 standarti tashkilotning atrof-muhitga ta'sirini tizimli boshqarishga yo'naltirilgan. Standart quyidagi asosiy tamoyillarga asoslanadi:

- **Atrof-muhit siyosati** — rahbariyat atrof-muhitni himoya qilish majburiyatini oladi
- **Rejalashtirish** — atrof-muhit jihatlarini aniqlash va xatarlarni baholash (§6.1)
- **Qo'llab-quvvatlash** — resurslar, kompetentlik, xabardorlik va aloqa (§7)
- **Faoliyat nazorati** — ifloslanishning oldini olish, chiqindilarni boshqarish (§8)
- **Ishlash baholash** — monitoring, o'lchash, audit (§9)
- **Yaxshilanish** — tuzatuvchi choralar va uzluksiz takomillashtirish (§10)

*Manba: ISO 14001:2015 §0.1 "Umumiy qoidalar", International Organization for Standardization, Geneva.*

## O'zbekistonda ISO 14001 Holati

O'zbekiston Standartlashtirish, Metrologiya va Sertifikatsiya Agentligi (UzDST) ISO 14001 ni O'zR DST ISO 14001:2015 sifatida qabul qilgan. Davlat ekologiya siyosati doirasida sanoat korxonalari uchun AMT joriy qilish tobora muhim ahamiyat kasb etmoqda.

Sertifikatsiya organlari:
- **UzDST akkreditatsiya markazi** — standart.uz
- Xalqaro organlar: Bureau Veritas, SGS, TÜV SÜD, DNV (barchasi O'zbekistonda vakolatxonaga ega)

*Manba: UzDST rasmiy sayti — standart.uz*

## ISO 14001:2015 Asosiy Bo'limlari

**§4 — Tashkilot konteksti:** Ichki va tashqi atrof-muhit omillarini tahlil qilish. Manfaatdor tomonlar (davlat organlari, mahalliy aholi, xaridorlar) talablarini aniqlash.

**§5 — Yetakchilik:** Rahbariyat atrof-muhit siyosatini e'lon qiladi va barcha bo'linmalarga yetkazadi. Mas'uliyatlar aniq belgilanadi.

**§6 — Rejalashtirish:** Tashkilotning atrof-muhit jihatlari (energiya sarfi, chiqindilar, emissiyalar) aniqlanadi va muhimliligi baholanadi. Huquqiy va boshqa talablar ro'yxati tuziladi.

**§7 — Qo'llab-quvvatlash:** Xodimlar tayyorlash, tashqi aloqa (ekologik hisobot), hujjatlashtirilgan axborot.

**§8 — Faoliyat:** Atrof-muhitga ta'sir etuvchi jarayonlarni nazorat qilish: chiqindilarni saralash, suvni tejash, energiya samaradorligi, favqulodda holatlarga tayyorlik.

**§9 — Ishlash baholash:** Atrof-muhit ko'rsatkichlari (energiya, suv, CO2 emissiyasi) o'lchanadi. Yillik ichki audit va rahbariyat ko'rib chiqishi o'tkaziladi.

**§10 — Yaxshilanish:** Nomuvofiqliklar bartaraf etiladi, uzluksiz takomillashtirish rejalari amalga oshiriladi.

## Sertifikatsiya Bosqichlari

### 1-bosqich: Dastlabki baholash va gap-tahlil (1–2 oy)

Joriy atrof-muhit menejmenti ISO 14001 talablari bilan solishtiriladi. Asosiy atrof-muhit jihatlari (energiya, suv, chiqindi, havo emissiyalari) aniqlanadi.

### 2-bosqich: AMT hujjatlarini tayyorlash (1–3 oy)

- Atrof-muhit siyosati va maqsadlarini ishlab chiqish
- Atrof-muhit jihatlarining reestri
- Huquqiy talablar ro'yxati (O'zbekiston ekologiya qonunchiligiga muvofiq)
- Favqulodda holatlarga tayyorlik rejasi

### 3-bosqich: Amaliyot va ichki audit (1–2 oy)

Joriy qilingan tizim real ish sharoitida sinovdan o'tkaziladi. ISO 14011 (ISO 19011) bo'yicha ichki audit o'tkaziladi.

### 4-bosqich: Sertifikatsiya auditi

Akkreditatsiya qilingan organ 2 bosqichli audit o'tkazadi: hujjatli tekshiruv (1–2 kun) va sahadagi audit (2–4 kun). Muvofiqlik tasdiqlangach 3 yillik sertifikat beriladi.

## Vaqt va Xarajatlar

| Bosqich | Vaqt | Taxminiy xarajat |
|---------|------|-----------------|
| Dastlabki gap-tahlil | 2–4 hafta | $500–$1,500 |
| Hujjatlar va joriy qilish | 2–4 oy | Maslahat: $2,000–$6,000 |
| Sertifikatsiya auditi | 1–2 oy | $1,500–$4,000 |
| Yillik kuzatuv | 1 oy/yil | $800–$1,500 |

*Eslatma: Narxlar tashkilot hajmi va akkreditatsiya organiga qarab farq qiladi. UzDST orqali mahalliy sertifikatsiya xarajati past bo'lishi mumkin.*

## ISO 14001 Foydasi

- **Eksport imkoniyatlari:** YeI, Xitoy va Koreya xaridorlari ISO 14001 ni tobora talab qilmoqda
- **Xarajatlarni kamaytirish:** Energiya va suv sarfini 10–25% qisqartirish mumkin (IFC ma'lumotlari)
- **Davlat soliq imtiyozlari:** O'zbekistonda yashil texnologiyalarni qo'llagan korxonalarga soliq imtiyozlari mavjud
- **Reputatsiya:** Atrof-muhit mas'uliyati korporativ brendni mustahkamlaydi

## Xulosa

ISO 14001:2015 — bu nafaqat sertifikat, balki korxonaning ekologik mas'uliyatini va samaradorligini oshirish tizimidir. O'zbekistondagi sanoat korxonalari uchun, ayniqsa eksportga yo'naltirilgan ishlab chiqaruvchilar uchun, bu standart raqobatbardoshlikni oshirishning kuchli vositasidir.

---

*Manbalar: ISO.org — "ISO 14001:2015 Environmental management systems – Requirements with guidance for use"; UzDST — standart.uz; ISO Survey of Certifications 2023; IFC — "Environmental Management Systems" guidelines.*''',
    },

    # ─────────────────────────────────────────────────────────────
    # ARTICLE 3 — ISO 14001:2015 Environmental Management  (RU)
    # ─────────────────────────────────────────────────────────────
    {
        'slug': 'iso-14001-2015-okruzhayushchaya-sreda-ru',
        'group_key': 'iso-14001-2015-env-management',
        'language': 'ru',
        'category_slug': 'sertifikatsiya',
        'category_name': 'Сертификация',
        'category_icon': '🏅',
        'is_featured': False,
        'read_time': 7,
        'cover_image': 'https://images.unsplash.com/photo-1441974231531-c6227db76b6e?w=1200&q=80',
        'title': 'ISO 14001:2015 Экологический менеджмент: Руководство для предприятий Узбекистана',
        'excerpt': 'ISO 14001:2015 — международный стандарт системы экологического менеджмента. В этой статье подробно описаны этапы сертификации для предприятий Узбекистана, требования UzDST и стоимость.',
        'content': '''ISO 14001:2015 — международный стандарт системы экологического менеджмента (СЭМ), издаваемый ISO. По данным ISO Survey 2023, более 400 000 организаций в 180+ странах имеют этот сертификат (источник: iso.org).

## Что такое ISO 14001:2015?

ISO 14001 направлен на системное управление воздействием организации на окружающую среду. Стандарт основан на следующих принципах:

- **Экологическая политика** — руководство принимает обязательства по охране окружающей среды
- **Планирование** — выявление экологических аспектов и оценка рисков (§6.1)
- **Обеспечение** — ресурсы, компетентность, осведомлённость, коммуникация (§7)
- **Операционный контроль** — предотвращение загрязнения, управление отходами (§8)
- **Оценка результативности** — мониторинг, измерение, аудит (§9)
- **Улучшение** — корректирующие действия и непрерывное совершенствование (§10)

*Источник: ISO 14001:2015 §0.1 "Общие положения", International Organization for Standardization, Geneva.*

## ISO 14001 в Узбекистане

Агентство UzDST приняло стандарт как O'zR DST ISO 14001:2015. В рамках государственной экологической политики внедрение СЭМ становится всё более важным для промышленных предприятий.

Органы по сертификации:
- **Аккредитационный центр UzDST** — standart.uz
- Международные органы: Bureau Veritas, SGS, TÜV SÜD, DNV (все с представительствами в Узбекистане)

*Источник: Официальный сайт UzDST — standart.uz*

## Основные разделы ISO 14001:2015

**§4 — Среда организации:** Анализ внутренних и внешних экологических факторов. Определение требований заинтересованных сторон (госорганы, местное население, покупатели).

**§5 — Лидерство:** Руководство провозглашает экологическую политику и доводит её до всех подразделений.

**§6 — Планирование:** Выявляются экологические аспекты (энергопотребление, выбросы, отходы) и оценивается их значимость. Составляется реестр правовых требований.

**§7 — Обеспечение:** Подготовка персонала, внешние коммуникации (экологическая отчётность), документированная информация.

**§8 — Деятельность:** Контроль процессов, влияющих на окружающую среду: сортировка отходов, экономия воды и энергии, готовность к аварийным ситуациям.

**§9 — Оценка результативности:** Измерение экологических показателей (энергия, вода, выбросы CO2). Ежегодный внутренний аудит и анализ со стороны руководства.

**§10 — Улучшение:** Устранение несоответствий, реализация планов непрерывного совершенствования.

## Этапы сертификации

### Этап 1: Предварительная оценка и анализ разрывов (1–2 месяца)

Текущий экологический менеджмент сравнивается с требованиями ISO 14001. Определяются ключевые экологические аспекты (энергия, вода, отходы, выбросы).

### Этап 2: Разработка документации СЭМ (1–3 месяца)

- Экологическая политика и цели
- Реестр экологических аспектов
- Перечень правовых требований (в соответствии с экологическим законодательством Узбекистана)
- План действий в аварийных ситуациях

### Этап 3: Практика и внутренний аудит (1–2 месяца)

Внедрённая система проверяется в реальных рабочих условиях. Проводится внутренний аудит по ISO 19011.

### Этап 4: Сертификационный аудит

Аккредитованный орган проводит двухстадийный аудит: проверка документов (1–2 дня) и аудит на месте (2–4 дня). После подтверждения соответствия выдаётся трёхлетний сертификат.

## Сроки и стоимость

| Этап | Срок | Ориентировочная стоимость |
|------|------|--------------------------|
| Предварительный анализ | 2–4 нед. | $500–$1 500 |
| Документация и внедрение | 2–4 мес. | Консалтинг: $2 000–$6 000 |
| Сертификационный аудит | 1–2 мес. | $1 500–$4 000 |
| Ежегодный надзор | 1 мес./год | $800–$1 500 |

*Стоимость варьируется в зависимости от размера организации и выбранного органа. Через UzDST сертификация может обойтись дешевле.*

## Преимущества ISO 14001

- **Экспортные возможности:** ЕС, Китай и Корея всё чаще требуют ISO 14001 от поставщиков
- **Сокращение затрат:** Снижение потребления энергии и воды на 10–25% (данные IFC)
- **Налоговые льготы:** В Узбекистане предприятиям, применяющим зелёные технологии, предоставляются льготы
- **Репутация:** Экологическая ответственность укрепляет корпоративный бренд

## Заключение

ISO 14001:2015 — это не просто сертификат, а система повышения экологической ответственности и эффективности предприятия. Для промышленных предприятий Узбекистана, особенно ориентированных на экспорт, этот стандарт является мощным инструментом повышения конкурентоспособности.

---

*Источники: ISO.org — "ISO 14001:2015 Environmental management systems – Requirements with guidance for use"; UzDST — standart.uz; ISO Survey of Certifications 2023; IFC — "Environmental Management Systems" guidelines.*''',
    },

    # ─────────────────────────────────────────────────────────────
    # ARTICLE 3 — ISO 14001:2015 Environmental Management  (EN)
    # ─────────────────────────────────────────────────────────────
    {
        'slug': 'iso-14001-2015-environmental-management-en',
        'group_key': 'iso-14001-2015-env-management',
        'language': 'en',
        'category_slug': 'sertifikatsiya',
        'category_name': 'Certification',
        'category_icon': '🏅',
        'is_featured': False,
        'read_time': 7,
        'cover_image': 'https://images.unsplash.com/photo-1441974231531-c6227db76b6e?w=1200&q=80',
        'title': 'ISO 14001:2015 Environmental Management: A Guide for Uzbekistan Businesses',
        'excerpt': 'ISO 14001:2015 is the international standard for environmental management systems. This article covers the certification steps, UzDST requirements, and costs for Uzbekistan companies.',
        'content': '''ISO 14001:2015 is the international standard for Environmental Management Systems (EMS), published by ISO. According to the ISO Survey of Certifications 2023 (iso.org), over 400,000 organizations in 180+ countries hold this certification.

## What Is ISO 14001:2015?

ISO 14001 provides a framework for organizations to systematically manage their environmental impact. The standard is built on these core principles:

- **Environmental policy** — top management commits to protecting the environment
- **Planning** — identifying environmental aspects and assessing risks (§6.1)
- **Support** — resources, competence, awareness, and communication (§7)
- **Operational control** — preventing pollution, managing waste (§8)
- **Performance evaluation** — monitoring, measurement, and audit (§9)
- **Improvement** — corrective actions and continual improvement (§10)

*Source: ISO 14001:2015 §0.1 "General", International Organization for Standardization, Geneva.*

## ISO 14001 in Uzbekistan

The Uzbekistan Agency for Technical Regulation (UzDST) has adopted the standard as O'zR DST ISO 14001:2015. As Uzbekistan's environmental legislation tightens and export markets demand green credentials, EMS certification is becoming increasingly important for industrial enterprises.

Certification bodies active in Uzbekistan:
- **UzDST Accreditation Centre** — standart.uz
- International bodies: Bureau Veritas, SGS, TÜV SÜD, DNV (all with local offices)

*Source: UzDST official website — standart.uz*

## Key Clauses of ISO 14001:2015

**§4 — Context of the organization:** Analyse internal and external environmental factors. Identify requirements of interested parties (regulators, local communities, customers).

**§5 — Leadership:** Management declares an environmental policy and communicates it throughout the organization. Roles and responsibilities are clearly defined.

**§6 — Planning:** Environmental aspects (energy use, emissions, water, waste) are identified and their significance rated. A register of legal requirements is compiled.

**§7 — Support:** Staff training, external communication (environmental reporting), and documented information management.

**§8 — Operation:** Control of processes that affect the environment: waste sorting, water and energy conservation, emergency preparedness.

**§9 — Performance evaluation:** Environmental indicators (energy, water, CO2 emissions) are measured. Annual internal audit and management review are conducted.

**§10 — Improvement:** Nonconformities are addressed, continual improvement plans are implemented.

## Certification Steps

### Step 1: Initial Assessment and Gap Analysis (1–2 months)

Current environmental management practices are compared against ISO 14001 requirements. Key environmental aspects (energy, water, waste, air emissions) are identified.

### Step 2: EMS Documentation (1–3 months)

- Develop environmental policy and objectives
- Compile register of environmental aspects
- List legal requirements (Uzbekistan environmental legislation)
- Draft emergency preparedness plan

### Step 3: Implementation and Internal Audit (1–2 months)

The implemented system is tested under real working conditions. An internal audit is conducted per ISO 19011 guidelines.

### Step 4: Certification Audit

An accredited body conducts a two-stage audit: document review (1–2 days) and on-site audit (2–4 days). A 3-year certificate is issued upon confirmed conformity.

## Timeline and Costs

| Stage | Duration | Estimated Cost |
|-------|----------|----------------|
| Initial gap analysis | 2–4 weeks | $500–$1,500 |
| Documentation & implementation | 2–4 months | Consulting: $2,000–$6,000 |
| Certification audit | 1–2 months | $1,500–$4,000 |
| Annual surveillance | 1 month/year | $800–$1,500 |

*Costs vary based on organization size and chosen certification body. UzDST-based certification may be more affordable.*

## Benefits of ISO 14001

- **Export access:** EU, Chinese, and Korean buyers increasingly require ISO 14001 from suppliers
- **Cost savings:** Energy and water consumption can be reduced by 10–25% (IFC data)
- **Tax incentives:** Uzbekistan offers tax benefits to enterprises applying green technologies
- **Reputation:** Environmental responsibility strengthens corporate brand and stakeholder trust

## Conclusion

ISO 14001:2015 is more than a certificate — it is a system for improving environmental responsibility and operational efficiency. For Uzbekistan's industrial enterprises, especially export-oriented manufacturers, this standard is a powerful tool for enhancing competitiveness in global markets.

---

*Sources: ISO.org — "ISO 14001:2015 Environmental management systems – Requirements with guidance for use"; UzDST — standart.uz; ISO Survey of Certifications 2023; IFC — "Environmental Management Systems" guidelines.*''',
    },

    # ─────────────────────────────────────────────────────────────
    # ARTICLE 4 — Halal Certification in Uzbekistan  (UZ)
    # ─────────────────────────────────────────────────────────────
    {
        'slug': 'halol-sertifikati-ozbekiston-uz',
        'group_key': 'halal-certification-uzbekistan',
        'language': 'uz',
        'category_slug': 'sertifikatsiya',
        'category_name': 'Sertifikatsiya',
        'category_icon': '🏅',
        'is_featured': False,
        'read_time': 6,
        'cover_image': 'https://images.unsplash.com/photo-1504674900247-0877df9cc836?w=1200&q=80',
        'title': 'Halol Sertifikati O\'zbekistonda: Jarayon, Xarajatlar va Eksport Imkoniyatlari',
        'excerpt': 'O\'zbekistonda halol sertifikati UzDST Halol markazi tomonidan beriladi. Ushbu maqolada qaysi mahsulotlarga halol sertifikati kerak, Qo\'lf mamlakatlari va Malayziyaga eksport, jarayon bosqichlari va xarajatlar batafsil yoritilgan.',
        'content': '''Halol sertifikati — mahsulot yoki xizmat Islom shariatiga muvofiq ekanligini tasdiqlovchi hujjat. O'zbekistonda aholining 93%+ i musulmonlar bo'lib, mahalliy bozor va eksport uchun halol sertifikati muhim ahamiyat kasb etmoqda.

## O'zbekistonda Halol Sertifikati Beruvchi Organ

O'zbekistonda halol sertifikatsiyasini **UzDST huzuridagi Halol sertifikatsiya markazi** amalga oshiradi. Markaz O'zbekiston Musulmonlar idorasi bilan hamkorlikda faoliyat yuritadi va xalqaro Halol standartlariga asoslanadi.

- **Rasmiy sayt:** standart.uz
- **Asosiy standart:** O'zR DST 2613 (Halol oziq-ovqat mahsulotlari umumiy talablar)
- **Xalqaro standart:** OIC/SMIIC 1:2019 — Halol Food General Requirements (Islom Hamkorlik Tashkiloti va SMIIC tomonidan tasdiqlangan)

*Manba: O'zbekiston Standartlashtirish, Metrologiya va Sertifikatsiya Agentligi — standart.uz; OIC/SMIIC — smiic.org*

## Qaysi Mahsulotlarga Halol Sertifikati Kerak?

**Oziq-ovqat mahsulotlari:**
- Go'sht va go'sht mahsulotlari (parrandachilik, qo'y, mol go'shti)
- Kolbasa, sausage, qayta ishlangan mahsulotlar
- Sut va sut mahsulotlari (tarkibida hayvon gelatini bo'lishi mumkin)
- Non va pishiriq mahsulotlari (alkogol yoki hayvon yog'i bo'lmasligi shart)
- Konserva va yarim tayyorlangan mahsulotlar
- Ichimliklar (alkogolsiz)

**Boshqa sohalar:**
- Dori-darmonlar va vitaminar (jelatin kapsulalar)
- Kosmetika va shaxsiy gigiena mahsulotlari
- Mehmonxona va restoran xizmatlari
- Logistika va omborxona (Halol logistics)

## Qo'lf Mamlakatlari va Malayziyaga Eksport

Halol sertifikati O'zbekiston eksportchilari uchun yangi bozorlar eshigini ochadi:

**Qo'lf hamkorlik kengashi (GCC) mamlakatlari:**
Saudi Arabiya, BAA, Qatar, Kuwait, Bahrayn, Ummon — jami 54 million iste'molchi. GCC halol importida taniqli sertifikatsiya organlari: ESMA (BAA), SFDA (Saudi Arabiya).

**Malayziya:** JAKIM (Jabatan Kemajuan Islam Malaysia) — Halol sertifikatsiyasida dunyodagi eng nufuzli organ. Malayziya O'zbekiston halol mahsulotlari uchun asosiy tranzit bozori hisoblanadi.

**Indoneziya:** BPJPH (Badan Penyelenggara Jaminan Produk Halal) — 270 million aholi bilan dunyodagi eng katta halol bozori.

*Manba: OIC/SMIIC — "Standards and Certification for Halal Products" (smiic.org); JAKIM rasmiy sayti*

## Sertifikatsiya Jarayoni

### 1-bosqich: Ariza berish

UzDST Halol markazi yoki akkreditatsiya qilingan organga ariza beriladi. Hujjatlar: korxona guvohnomalari, mahsulot tarkibi, ishlab chiqarish texnologiyasi.

### 2-bosqich: Hujjatlarni tekshirish

Mutaxassislar mahsulot tarkibini, xom ashyo manbalarini va ishlab chiqarish texnologiyasini tekshiradi. Harom moddalar (cho'chqa go'shti, alkogol, qon va boshqalar) yo'qligi aniqlanadi.

### 3-bosqich: Korxona auditi

Inspektor ishlab chiqarish joyiga keladi va quyidagilarni tekshiradi:
- Xom ashyo saqlash va ajratish (Halol va non-Halol mahsulotlar aralashmasligi)
- Tozalash va dezinfektsiya protseduralari
- Xodimlar tayyorgarligi va bilimi
- Yorliqlar va qadoqlash

### 4-bosqich: Sertifikat berish

Muvofiqlik tasdiqlangach, halol sertifikati beriladi. Sertifikat muddati odatda **1 yil** (ba'zi hollarda 2 yil), shundan so'ng kuzatuv auditi o'tkaziladi.

## Vaqt va Xarajatlar

| Bosqich | Vaqt | Taxminiy xarajat |
|---------|------|-----------------|
| Ariza va hujjatlar | 1–2 hafta | $100–$300 |
| Hujjatlar tekshiruvi | 2–4 hafta | Sertifikatsiya to'loviga kiradi |
| Korxona auditi | 1–3 kun | $500–$2,000 |
| Sertifikat va yorliq | 1–2 hafta | $300–$800 |
| **Jami** | **1–3 oy** | **$1,000–$3,500** |

*Narxlar mahsulot turiga, korxona hajmiga va sertifikatsiya organiga qarab farq qiladi. GCC yoki Malayziya bozoriga yo'naltirilgan sertifikatsiya uchun xalqaro organ tanlanishi mumkin — narxi yuqoriroq.*

## Halol Sertifikatining Foydasi

- **Mahalliy bozor:** O'zbekiston supermarketlari va tarmoq do'konlari halol yorlig'li mahsulotlarga talabni oshirmoqda
- **Eksport:** GCC mamlakatlariga eksport uchun halol sertifikati majburiy shart
- **Brendlash:** Halol yorlig'i global e'tirof qilingan sifat belgisiga aylanib bormoqda
- **Ishonch:** Iste'molchilar halol mahsulotlarga yuqori ishonch bildiradi — qaytib keluvchi mijozlar ko'p

## Xulosa

O'zbekiston korxonalari uchun halol sertifikati nafaqat diniy majburiyat, balki kuchli biznes vositasidir. Milliy va xalqaro halol bozorining o'sishi fonida sertifikatlangan korxonalar yangi eksport shartnomalari va sherikliklar uchun keng imkoniyatlarga ega bo'ladi.

---

*Manbalar: UzDST Halol sertifikatsiya markazi — standart.uz; OIC/SMIIC 1:2019 "Halal Food – General Requirements"; JAKIM — halal.gov.my; BPJPH — halal.go.id.*''',
    },

    # ─────────────────────────────────────────────────────────────
    # ARTICLE 4 — Halal Certification in Uzbekistan  (RU)
    # ─────────────────────────────────────────────────────────────
    {
        'slug': 'halyal-sertifikat-uzbekistan-ru',
        'group_key': 'halal-certification-uzbekistan',
        'language': 'ru',
        'category_slug': 'sertifikatsiya',
        'category_name': 'Сертификация',
        'category_icon': '🏅',
        'is_featured': False,
        'read_time': 6,
        'cover_image': 'https://images.unsplash.com/photo-1504674900247-0877df9cc836?w=1200&q=80',
        'title': 'Халяль-сертификация в Узбекистане: Процесс, Стоимость и Экспортные Возможности',
        'excerpt': 'Халяль-сертификат в Узбекистане выдаётся Халяль-центром UzDST. В статье рассмотрены: какие продукты нуждаются в сертификации, экспорт в страны Залива и Малайзию, этапы процесса и стоимость.',
        'content': '''Халяль-сертификат подтверждает, что продукт или услуга соответствует нормам исламского шариата. В Узбекистане, где более 93% населения составляют мусульмане, халяль-сертификация имеет важное значение как для внутреннего рынка, так и для экспорта.

## Орган по халяль-сертификации в Узбекистане

Халяль-сертификацию в Узбекистане осуществляет **Центр халяль-сертификации при UzDST**, работающий в сотрудничестве с Управлением мусульман Узбекистана. Деятельность основана на международных халяль-стандартах.

- **Официальный сайт:** standart.uz
- **Основной стандарт:** O'zR DST 2613 (Продукты питания халяль — общие требования)
- **Международный стандарт:** OIC/SMIIC 1:2019 — Halal Food General Requirements (утверждён Организацией исламского сотрудничества и SMIIC)

*Источник: Агентство UzDST — standart.uz; OIC/SMIIC — smiic.org*

## Какие продукты нуждаются в халяль-сертификации?

**Продукты питания:**
- Мясо и мясопродукты (птица, баранина, говядина)
- Колбасы, сосиски, переработанные продукты
- Молоко и молочные продукты (возможно содержание животного желатина)
- Хлебобулочные изделия (недопустимо использование алкоголя или животных жиров)
- Консервы и полуфабрикаты
- Безалкогольные напитки

**Другие категории:**
- Лекарственные препараты и витамины (желатиновые капсулы)
- Косметика и средства личной гигиены
- Гостиничные и ресторанные услуги
- Логистика и складирование (Halal logistics)

## Экспорт в страны Залива и Малайзию

Халяль-сертификат открывает новые рынки для узбекских экспортёров:

**Совет сотрудничества арабских государств Залива (ССАГЗ):**
Саудовская Аравия, ОАЭ, Катар, Кувейт, Бахрейн, Оман — 54 млн потребителей. Ведущие органы по халяль-сертификации в регионе: ESMA (ОАЭ), SFDA (Саудовская Аравия).

**Малайзия:** JAKIM (Jabatan Kemajuan Islam Malaysia) — один из наиболее авторитетных органов в мире. Малайзия является ключевым транзитным рынком для халяль-продукции из Узбекистана.

**Индонезия:** BPJPH (Badan Penyelenggara Jaminan Produk Halal) — крупнейший халяль-рынок мира с населением 270 млн человек.

*Источник: OIC/SMIIC — "Standards and Certification for Halal Products" (smiic.org); официальный сайт JAKIM*

## Этапы сертификации

### Этап 1: Подача заявки

Заявка подаётся в Центр халяль-сертификации UzDST или аккредитованный орган. Документы: свидетельства предприятия, состав продукта, технология производства.

### Этап 2: Проверка документации

Специалисты проверяют состав продукта, источники сырья и технологию производства. Устанавливается отсутствие харамных ингредиентов (свинина, алкоголь, кровь и др.).

### Этап 3: Аудит предприятия

Инспектор выезжает на производство и проверяет:
- Хранение и разделение сырья (исключить смешение халяль и не-халяль)
- Процедуры уборки и дезинфекции
- Обученность и осведомлённость персонала
- Маркировку и упаковку

### Этап 4: Выдача сертификата

После подтверждения соответствия выдаётся халяль-сертификат сроком обычно **1 год** (в ряде случаев 2 года), затем проводится надзорный аудит.

## Сроки и стоимость

| Этап | Срок | Ориентировочная стоимость |
|------|------|--------------------------|
| Заявка и документы | 1–2 нед. | $100–$300 |
| Проверка документов | 2–4 нед. | Включено в сертификационный сбор |
| Аудит предприятия | 1–3 дня | $500–$2 000 |
| Сертификат и маркировка | 1–2 нед. | $300–$800 |
| **Итого** | **1–3 месяца** | **$1 000–$3 500** |

*Стоимость зависит от вида продукции, размера предприятия и органа сертификации. Для экспорта в ОАЭ/Малайзию может потребоваться международный орган — стоимость будет выше.*

## Преимущества халяль-сертификации

- **Внутренний рынок:** Супермаркеты и торговые сети Узбекистана всё активнее требуют халяль-маркировку
- **Экспорт:** Для экспорта в страны ССАГЗ наличие халяль-сертификата является обязательным
- **Брендинг:** Халяль-маркировка становится глобально признанным знаком качества
- **Доверие потребителей:** Лояльность к халяль-брендам традиционно высока, что обеспечивает повторные покупки

## Заключение

Для узбекских предприятий халяль-сертификация — это не только религиозное требование, но и мощный инструмент бизнеса. На фоне роста национального и международного халяль-рынка сертифицированные компании получают широкие возможности для новых экспортных контрактов и партнёрств.

---

*Источники: Центр халяль-сертификации UzDST — standart.uz; OIC/SMIIC 1:2019 "Halal Food – General Requirements"; JAKIM — halal.gov.my; BPJPH — halal.go.id.*''',
    },

    # ─────────────────────────────────────────────────────────────
    # ARTICLE 4 — Halal Certification in Uzbekistan  (EN)
    # ─────────────────────────────────────────────────────────────
    {
        'slug': 'halal-certification-uzbekistan-en',
        'group_key': 'halal-certification-uzbekistan',
        'language': 'en',
        'category_slug': 'sertifikatsiya',
        'category_name': 'Certification',
        'category_icon': '🏅',
        'is_featured': False,
        'read_time': 6,
        'cover_image': 'https://images.unsplash.com/photo-1504674900247-0877df9cc836?w=1200&q=80',
        'title': 'Halal Certification in Uzbekistan: Process, Costs and Export Opportunities',
        'excerpt': 'Halal certification in Uzbekistan is issued by the UzDST Halal Centre. This article covers which products need certification, exporting to Gulf countries and Malaysia, the full process steps, and costs.',
        'content': '''A Halal certificate confirms that a product or service complies with Islamic Sharia law. In Uzbekistan, where over 93% of the population is Muslim, Halal certification is significant both for the domestic market and for export to Muslim-majority countries worldwide.

## Halal Certification Authority in Uzbekistan

Halal certification in Uzbekistan is carried out by the **Halal Certification Centre under UzDST**, operating in cooperation with the Muslim Board of Uzbekistan. The centre's work is grounded in international Halal standards.

- **Official website:** standart.uz
- **National standard:** O'zR DST 2613 (Halal food products — General requirements)
- **International standard:** OIC/SMIIC 1:2019 — Halal Food General Requirements (endorsed by the Organisation of Islamic Cooperation and SMIIC)

*Source: UzDST — standart.uz; OIC/SMIIC — smiic.org*

## Which Products Need Halal Certification?

**Food products:**
- Meat and meat products (poultry, lamb, beef)
- Sausages, processed meat products
- Dairy products (may contain animal-derived gelatin)
- Bakery products (no alcohol or animal fats permitted)
- Canned goods and semi-prepared foods
- Non-alcoholic beverages

**Other categories:**
- Medicines and vitamins (gelatin capsules)
- Cosmetics and personal care products
- Hotel and restaurant services
- Logistics and warehousing (Halal logistics)

## Exporting to Gulf Countries and Malaysia

A Halal certificate opens new markets for Uzbekistan exporters:

**Gulf Cooperation Council (GCC):**
Saudi Arabia, UAE, Qatar, Kuwait, Bahrain, Oman — 54 million consumers. Leading Halal certification bodies in the region: ESMA (UAE), SFDA (Saudi Arabia).

**Malaysia:** JAKIM (Jabatan Kemajuan Islam Malaysia) — one of the world's most authoritative Halal certification bodies. Malaysia serves as a key transit market for Uzbekistan's Halal products.

**Indonesia:** BPJPH (Badan Penyelenggara Jaminan Produk Halal) — the world's largest Halal market with 270 million people.

*Source: OIC/SMIIC — "Standards and Certification for Halal Products" (smiic.org); JAKIM official website*

## Certification Process

### Step 1: Application

An application is submitted to the UzDST Halal Certification Centre or an accredited body. Required documents: company registration certificates, product composition, and production technology descriptions.

### Step 2: Document Review

Specialists review the product composition, raw material sources, and production technology. The absence of haram ingredients (pork, alcohol, blood, etc.) is verified.

### Step 3: Factory Audit

An inspector visits the production facility and checks:
- Storage and separation of raw materials (preventing mixing of Halal and non-Halal)
- Cleaning and disinfection procedures
- Staff training and awareness
- Labelling and packaging compliance

### Step 4: Certificate Issuance

Upon confirmed conformity, the Halal certificate is issued — typically valid for **1 year** (sometimes 2), after which a surveillance audit is conducted.

## Timeline and Costs

| Stage | Duration | Estimated Cost |
|-------|----------|----------------|
| Application and documents | 1–2 weeks | $100–$300 |
| Document review | 2–4 weeks | Included in certification fee |
| Factory audit | 1–3 days | $500–$2,000 |
| Certificate and labelling | 1–2 weeks | $300–$800 |
| **Total** | **1–3 months** | **$1,000–$3,500** |

*Costs vary by product type, company size, and chosen certification body. For UAE/Malaysia markets, an internationally recognised body may be required — at higher cost.*

## Benefits of Halal Certification

- **Domestic market:** Uzbekistan supermarkets and retail chains are increasingly demanding Halal labelling
- **Export:** Halal certification is a mandatory requirement for exporting to GCC member states
- **Branding:** The Halal mark is becoming a globally recognised quality signal
- **Consumer trust:** Loyalty to Halal brands is traditionally high, resulting in strong repeat purchase rates

## Conclusion

For Uzbekistan businesses, Halal certification is not only a religious obligation but a powerful commercial tool. As both the national and global Halal market continues to grow, certified companies are well positioned to secure new export contracts and partnerships across Muslim-majority markets worldwide.

---

*Sources: UzDST Halal Certification Centre — standart.uz; OIC/SMIIC 1:2019 "Halal Food – General Requirements"; JAKIM — halal.gov.my; BPJPH — halal.go.id.*''',
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
