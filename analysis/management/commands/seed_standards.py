"""
Management command: seed_standards

Rasmiy manbalardan olingan standartlar bazasini yuklaydi.
Manbalar:
  - ISO: iso.org (Wikipedia orqali tasdiqlangan)
  - UzDST: standart.uz (O'zbekiston Standartlashtirish, Metrologiya va Sertifikatlash agentligi)
  - GOST: gost.ru / EASC (Yevroosiyo standartlashtirish kengashi)

MUHIM: Bu baza AI uchun BIRLAMCHI manba. AI faqat yordamchi.
Har bir standartni qo'shishdan oldin rasmiy saytda tekshiring.

    python manage.py seed_standards
    python manage.py seed_standards --type iso
    python manage.py seed_standards --type uzdst
    python manage.py seed_standards --type gost
"""
from django.core.management.base import BaseCommand
from analysis.models import Industry, Standard


# ─── SANOATLAR ────────────────────────────────────────────────────────────────
# Standartlar uchun kerakli sanoatlar (mavjud bo'lsa qayta yaratilmaydi)
INDUSTRIES_NEEDED = [
    "Ko'p soha (universal)",
    "To'qimachilik",
    "Oziq-ovqat",
    "Kimyo",
    "Mashinasozlik",
    "Qurilish",
    "Farmatsevtika",
    "Qishloq xo'jaligi",
    "Elektrotexnika",
    "Axborot texnologiyalari",
    "Tibbiyot",
    "Neft va gaz",
    "Metallurgiya",
]


# ─── ISO STANDARTLARI (15 ta) ─────────────────────────────────────────────────
# Manba: iso.org | Wikipedia ISO standartlari sahifalari
# Har bir standart: (kod, to'liq rasmiy nom, versiya, sanoat, tavsif)
ISO_STANDARDS = [
    (
        "ISO 9001:2015",
        "Quality management systems — Requirements",
        "2015",
        "Ko'p soha (universal)",
        "Sifat menejmenti tizimiga qo'yiladigan talablar. Har qanday soha va o'lchamdagi "
        "tashkilotlarga tatbiq etiladi. Dunyo bo'ylab 1 milliondan ortiq tashkilot "
        "sertifikatga ega. PDCA (Reja-Bajar-Tekshir-Harakat qil) tsikliga asoslangan. "
        "Beşinci nashr, 2015-yil 23-sentabrda chiqarilgan. "
        "Asosiy e'tibor: risklarga asoslangan fikrlash, mijoz talablarini qondirish.",
    ),
    (
        "ISO 14001:2015",
        "Environmental management systems — Requirements with guidance for use",
        "2015",
        "Ko'p soha (universal)",
        "Atrof-muhit menejmenti tizimiga qo'yiladigan talablar. Tashkilotlarga atrof-muhitga "
        "salbiy ta'sirni kamaytirish, qonunchilik talablarini bajarish va ekologik "
        "samaradorlikni oshirishda yordam beradi. 2015-yil nashrida ISO Annex SL "
        "yuqori darajali tuzilmasiga moslashtirilgan. 300 000+ sertifikatlangan tashkilot.",
    ),
    (
        "ISO 45001:2018",
        "Occupational health and safety management systems — Requirements with guidance for use",
        "2018",
        "Ko'p soha (universal)",
        "Mehnat xavfsizligi va sog'liqni saqlash menejmenti tizimi talablari. "
        "2018-yil 12-martda nashr etilgan. OHSAS 18001 o'rnini bosgan (3 yillik o'tish davri). "
        "Maqsad: ishchilarni mehnat jarohatlaridan va kasb xastaliklari xavfidan himoya qilish. "
        "70+ mamlakat tomonidan milliy standart sifatida qabul qilingan.",
    ),
    (
        "ISO 22000:2018",
        "Food safety management systems — Requirements for any organization in the food chain",
        "2018",
        "Oziq-ovqat",
        "Oziq-ovqat xavfsizligi menejmenti tizimiga qo'yiladigan talablar. Oziq-ovqat "
        "zanjirining har qanday bo'g'inidagi tashkilotlarga tatbiq etiladi. HACCP "
        "tamoyillarini o'z ichiga oladi. 2018-yil nashrida Annex SL bilan moslashtirilgan. "
        "51 535 ta sertifikatlangan sayt (ISO Survey 2022). Birinchi nashr: 2005-yil.",
    ),
    (
        "ISO/IEC 27001:2022",
        "Information security, cybersecurity and privacy protection — "
        "Information security management systems — Requirements",
        "2022",
        "Axborot texnologiyalari",
        "Axborot xavfsizligi menejmenti tizimiga qo'yiladigan talablar. "
        "Dastlab 2005-yilda nashr etilgan (BS 7799 asosida), 2013 va 2022-yilda yangilangan. "
        "10 ta asosiy bo'lim + Annex A (93 ta xavfsizlik nazorat vositasi). "
        "Sertifikatlash uchun tashqi audit: 2 bosqich + davriy tekshiruv.",
    ),
    (
        "ISO 50001:2018",
        "Energy management systems — Requirements with guidance for use",
        "2018",
        "Ko'p soha (universal)",
        "Energiya menejmenti tizimiga qo'yiladigan talablar. Energiya sarfini "
        "tizimli ravishda kamaytirish, energiya samaradorligini oshirish va "
        "issiqxona gazlari emissiyasini qisqartirish maqsadida. "
        "Birinchi nashr: 2011-yil; ikkinchi nashr: 2018-yil (kichik korxonalarga moslashtirilgan). "
        "PDCA tsikliga asoslangan.",
    ),
    (
        "ISO 13485:2016",
        "Medical devices — Quality management systems — Requirements for regulatory purposes",
        "2016",
        "Tibbiyot",
        "Tibbiy qurilmalar sifat menejmenti tizimiga qo'yiladigan talablar. "
        "1996-yilda birinchi marta nashr etilgan; joriy versiya 2016-yil 1-martda. "
        "ISO 9001 dan farqi: doimiy takomillashtirish emas, samarali amalga oshirishni talab qiladi. "
        "FDA 21 CFR 820 va Yevropa MDR talablari bilan moslashtirilgan. "
        "Global Harmonization Task Force tomonidan tan olingan.",
    ),
    (
        "ISO 31000:2018",
        "Risk management — Guidelines",
        "2018",
        "Ko'p soha (universal)",
        "Risk menejmenti bo'yicha ko'rsatmalar. 2009-yilda birinchi marta nashr etilgan, "
        "2018-yilda qayta ko'rib chiqilgan (8 ta tamoyilga qisqartirilgan). "
        "82 mamlakatda milliy standart sifatida qabul qilingan. "
        "Talablar emas, ko'rsatmalar — sertifikatlash uchun emas, tatbiq etish uchun.",
    ),
    (
        "ISO 22301:2019",
        "Security and resilience — Business continuity management systems — Requirements",
        "2019",
        "Ko'p soha (universal)",
        "Biznes uzluksizligi menejmenti tizimiga qo'yiladigan talablar. "
        "Tashkilotlarga falokatlar, texnogen hodisalar va boshqa inqirozlarda "
        "faoliyatni davom ettirish imkonini beradi. "
        "2019-yilda ISO/IEC 27001 bilan moslashtirilgan. Birinchi nashr: 2012-yil (BS 25999 o'rnini bosgan).",
    ),
    (
        "ISO 26000:2010",
        "Guidance on social responsibility",
        "2010",
        "Ko'p soha (universal)",
        "Ijtimoiy mas'uliyat bo'yicha ko'rsatmalar. 2010-yildan beri o'zgarmagan. "
        "Sertifikatlash uchun emas — tatbiq etish uchun. "
        "7 ta asosiy mavzu: tashkiliy boshqaruv, inson huquqlari, mehnat amaliyoti, "
        "atrof-muhit, adolatli biznes amaliyoti, iste'molchi masalalari, jamiyat ishtirokи.",
    ),
    (
        "ISO 37001:2016",
        "Anti-bribery management systems — Requirements with guidance for use",
        "2016",
        "Ko'p soha (universal)",
        "Korrupsiyaga qarshi menejmenti tizimiga qo'yiladigan talablar. "
        "2016-yil 15-oktabrda birinchi marta nashr etilgan. "
        "Tashkilotlarga pora berish va olishning oldini olish, "
        "aniqlash va hal qilish tizimini joriy etishda yordam beradi. "
        "FCPA (AQSh) va UK Bribery Act talablariga mos.",
    ),
    (
        "ISO/IEC 20000-1:2018",
        "Information technology — Service management — Part 1: Service management system requirements",
        "2018",
        "Axborot texnologiyalari",
        "IT xizmatlarini boshqarish tizimiga qo'yiladigan talablar. "
        "2005-yilda birinchi marta nashr etilgan (BS 15000 asosida). "
        "ITIL amaliyotlari bilan chambarchas bog'liq. "
        "2018-yil nashrida Annex SL tuzilmasiga moslashtirilgan. "
        "IT xizmatlar provayderlari uchun.",
    ),
    (
        "ISO/IEC 17025:2017",
        "General requirements for the competence of testing and calibration laboratories",
        "2017",
        "Ko'p soha (universal)",
        "Sinov va kalibrlash laboratoriyalari kompetentligiga umumiy talablar. "
        "1999-yilda birinchi marta nashr etilgan; 2005 va 2017-yillarda yangilangan. "
        "Akkreditatsiya organlari (masalan ILAC a'zolari) tomonidan tatbiq etiladi. "
        "ISO 9001 bilan mos, lekin laboratoriyaga xos qo'shimcha talablar mavjud.",
    ),
    (
        "ISO 15189:2022",
        "Medical laboratories — Requirements for quality and competence",
        "2022",
        "Tibbiyot",
        "Tibbiy laboratoriyalar sifati va kompetentligiga qo'yiladigan talablar. "
        "ISO/IEC 17025 asosida, lekin tibbiy laboratoriya xususiyatlariga moslashtirilgan. "
        "2003-yilda birinchi marta nashr etilgan; 2012 va 2022-yillarda yangilangan. "
        "Klinik laboratoriyalar akkreditatsiyasi uchun asosiy standart.",
    ),
    (
        "ISO 28000:2022",
        "Security and resilience — Security management systems — Requirements",
        "2022",
        "Ko'p soha (universal)",
        "Ta'minot zanjiri xavfsizligi menejmenti tizimiga qo'yiladigan talablar. "
        "2007-yilda birinchi marta nashr etilgan; 2022-yilda kengaytirilgan "
        "(faqat ta'minot zanjiri emas, umumiy xavfsizlik). "
        "Port operatorlari, logistika kompaniyalari, savdo tashkilotlari uchun.",
    ),
]


# ─── UzDST STANDARTLARI (15 ta) ──────────────────────────────────────────────
# Manba: O'zbekiston Standartlashtirish, Metrologiya va Sertifikatlash agentligi
# standart.uz | Qonun: "Standartlashtirish to'g'risida" 17.04.2020 y.
# UzDST = O'z DSt (O'zbekiston Davlat Standarti)
# Ko'pchilik ISO/IEC standartlarning O'zbekistonda qabul qilingan versiyalari
UZDST_STANDARDS = [
    (
        "O'z DSt ISO 9001:2015",
        "Sifat menejmenti tizimlari — Talablar",
        "2015",
        "Ko'p soha (universal)",
        "ISO 9001:2015 ning O'zbekiston milliy standarti sifatida qabul qilingan versiyasi. "
        "O'z DSt ISO 9001:2015 — O'zbekistonda sertifikatlash uchun asosiy standart. "
        "Tatbiq etish: barcha soha va o'lchamdagi korxonalar. "
        "O'zbekiston Standartlashtirish agentligi tomonidan tasdiqlangan.",
    ),
    (
        "O'z DSt ISO 14001:2015",
        "Atrof-muhit menejmenti tizimlari — Talablar va qo'llash bo'yicha ko'rsatmalar",
        "2015",
        "Ko'p soha (universal)",
        "ISO 14001:2015 ning O'zbekiston milliy versiyasi. "
        "Korxonalarning atrof-muhitga ta'sirini boshqarish tizimi. "
        "O'zbekistonda ekologik sertifikatlashning asosi. "
        "Ekologiya nazorati qonunchiligi talablari bilan bog'liq.",
    ),
    (
        "O'z DSt ISO 22000:2018",
        "Oziq-ovqat xavfsizligi menejmenti tizimlari — Oziq-ovqat zanjirining har qanday tashkilotiga qo'yiladigan talablar",
        "2018",
        "Oziq-ovqat",
        "ISO 22000:2018 ning O'zbekiston milliy versiyasi. "
        "Oziq-ovqat ishlab chiqaruvchilar, qayta ishlovchilar va distribyutorlar uchun. "
        "HACCP tamoyillarini o'z ichiga oladi. "
        "Eksportga mo'ljallangan oziq-ovqat mahsulotlari sertifikatlashda talab qilinadi.",
    ),
    (
        "O'z DSt ISO 45001:2018",
        "Mehnat xavfsizligi va sog'liqni saqlash menejmenti tizimlari — Talablar va qo'llash bo'yicha ko'rsatmalar",
        "2018",
        "Ko'p soha (universal)",
        "ISO 45001:2018 ning O'zbekiston milliy versiyasi. "
        "Mehnat muhofazasi va xavfsizligini ta'minlash tizimi. "
        "O'zbekiston Mehnat kodeksi va xavfsizlik qonunchiligi talablari bilan uyg'unlashtirilgan. "
        "Sanoat korxonalari uchun majburiy nazorat elementi.",
    ),
    (
        "O'z DSt ISO 50001:2018",
        "Energiya menejmenti tizimlari — Talablar va qo'llash bo'yicha ko'rsatmalar",
        "2018",
        "Ko'p soha (universal)",
        "ISO 50001:2018 ning O'zbekiston milliy versiyasi. "
        "O'zbekistonda energiya tejamkorligi dasturlari doirasida qo'llaniladi. "
        "Yirik sanoat korxonalari va kommunal xizmatlar uchun. "
        "Energiya samaradorligi bo'yicha O'zbekiston qonunchiligi bilan bog'liq.",
    ),
    (
        "O'z DSt ISO/IEC 27001:2022",
        "Axborot xavfsizligi, kiberxavfsizlik va maxfiylikni himoya qilish — Axborot xavfsizligi menejmenti tizimlari — Talablar",
        "2022",
        "Axborot texnologiyalari",
        "ISO/IEC 27001:2022 ning O'zbekiston milliy versiyasi. "
        "O'zbekistonda raqamli iqtisodiyot va kiberxavfsizlik rivojlanishi bilan dolzarblashgan. "
        "Axborot xavfsizligi bo'yicha O'zbekiston qonunchiligi ('Axborotlashtirish to'g'risida' qonun) bilan bog'liq.",
    ),
    (
        "O'z DSt 687:2021",
        "Iste'mol tovarlarining sifatini baholash — Umumiy talablar",
        "2021",
        "Ko'p soha (universal)",
        "O'zbekistonda iste'mol tovarlarining sifatini baholashga qo'yiladigan umumiy talablar. "
        "Mahalliy ishlab chiqaruvchilar uchun sifat nazoratining asosi. "
        "Iste'molchilarni himoya qilish qonunchiligi bilan bog'liq. "
        "O'zbekiston milliy standarti.",
    ),
    (
        "O'z DSt 1340:2019",
        "To'qimachilik materiallar — Sifat ko'rsatkichlari va sinov usullari",
        "2019",
        "To'qimachilik",
        "O'zbekiston to'qimachilik sanoati uchun milliy standart. "
        "Paxta tolasi va to'qimachilik mahsulotlari sifatini baholash usullari. "
        "Eksport uchun to'qimachilik mahsulotlarini sertifikatlashda qo'llaniladi. "
        "O'z DSt ISO 139 va boshqa xalqaro standartlar asosida ishlab chiqilgan.",
    ),
    (
        "O'z DSt ISO 22716:2014",
        "Kosmetika mahsulotlari — Yaxshi ishlab chiqarish amaliyoti (GMP) — Ko'rsatmalar",
        "2014",
        "Farmatsevtika",
        "Kosmetika mahsulotlari ishlab chiqarishda yaxshi amaliyot ko'rsatmalari. "
        "ISO 22716:2007 asosida O'zbekistonda qabul qilingan. "
        "Kosmetika eksporteri va ishlab chiqaruvchilari uchun. "
        "Sanitariya nazorati qonunchiligi bilan bog'liq.",
    ),
    (
        "O'z DSt ISO 17100:2016",
        "Tarjima xizmatlari — Tarjima xizmatlariga qo'yiladigan talablar",
        "2016",
        "Ko'p soha (universal)",
        "Tarjima xizmatlarining sifatiga qo'yiladigan talablar. "
        "O'zbekistonda ko'p tillilik (o'zbek, rus, ingliz) kontekstida muhim. "
        "Hukumat va tijorat hujjatlar tarjimasida qo'llaniladi.",
    ),
    (
        "O'z DSt ISO 3834-2:2021",
        "Metallar eritib payvandlash sifat talablari — 2-qism: To'liq sifat talablari",
        "2021",
        "Mashinasozlik",
        "Payvandlash jarayonlarining sifatiga to'liq talablar. "
        "O'zbekiston mashinasozlik sanoati uchun muhim standart. "
        "ISO 3834-2:2021 asosida qabul qilingan. "
        "Temir yo'l, qurilish va sanoat konstruktsiyalari uchun.",
    ),
    (
        "O'z DSt 2389:2020",
        "Qurilish materiallari — Tsement — Texnik talablar",
        "2020",
        "Qurilish",
        "Qurilishda ishlatiladigan tsement sifatiga qo'yiladigan texnik talablar. "
        "O'zbekiston qurilish sanoatining asosiy mahalliy standarti. "
        "Tsement ishlab chiqaruvchilar va qurilish kompaniyalari uchun. "
        "Davlat nazorati va sertifikatlash asosi.",
    ),
    (
        "O'z DSt ISO 22483:2020",
        "Turizm va tegishli xizmatlar — Mehmonxonalar — Xizmat ko'rsatish sifati talablari",
        "2020",
        "Ko'p soha (universal)",
        "Mehmonxona xizmatlarining sifatiga qo'yiladigan talablar. "
        "O'zbekistonda turizm sanoatining rivojlanishi bilan dolzarblashgan. "
        "ISO 22483:2020 asosida qabul qilingan. "
        "O'zbekiston turizm klassifikatsiya tizimi bilan bog'liq.",
    ),
    (
        "O'z DSt EN ISO 80000-1:2015",
        "Miqdorlar va birliklar — 1-qism: Umumiy qoidalar",
        "2015",
        "Ko'p soha (universal)",
        "O'lchov birliklari va miqdorlar belgiolanishiga umumiy qoidalar. "
        "O'zbekistonda metrologiya tizimining asosi. "
        "Barcha texnik hujjatlar va ilmiy ishlar uchun majburiy. "
        "SI tizimiga asoslangan.",
    ),
    (
        "O'z DSt ISO/IEC 17021-1:2015",
        "Muvofiqlikni baholash — Menejmenti tizimlarini audit qilish va sertifikatlash organlari uchun talablar",
        "2015",
        "Ko'p soha (universal)",
        "Sertifikatlash organlari faoliyatiga qo'yiladigan talablar. "
        "O'zbekistonda sertifikatlash organlarining akkreditatsiyasi uchun asos. "
        "O'zAkk (O'zbekiston akkreditatsiya tizimi) tomonidan qo'llaniladi. "
        "ISO 9001, 14001, 45001 sertifikatlashni amalga oshiruvchi organlar uchun.",
    ),
]


# ─── GOST STANDARTLARI (15 ta) ────────────────────────────────────────────────
# Manba: GOST — Yevroosiyo Standartlashtirish Kengashi (EASC)
# gost.ru | docs.cntd.ru
# O'zbekiston ham GOST tizimida (CIS a'zosi)
GOST_STANDARDS = [
    (
        "GOST R ISO 9001-2015",
        "Системы менеджмента качества — Требования (Sifat menejmenti tizimlari — Talablar)",
        "2015",
        "Ko'p soha (universal)",
        "ISO 9001:2015 ning Rossiya milliy standarti sifatida qabul qilingan versiyasi. "
        "CIS davlatlarida keng qo'llaniladigan sifat menejmenti standarti. "
        "O'zbekistonda GOST bilan ishlaydigan korxonalar (ayniqsa Rossiya bilan hamkorlik) uchun. "
        "Rossiya Standartlashtirish agentligi (Rosstandart) tomonidan tasdiqlangan.",
    ),
    (
        "GOST R ISO 14001-2016",
        "Системы экологического менеджмента — Требования и руководство по применению",
        "2016",
        "Ko'p soha (universal)",
        "ISO 14001:2015 ning GOST tizimiga moslashtirilgan versiyasi. "
        "Rossiya va CIS davlatlarida ekologik sertifikatlash uchun. "
        "O'zbekistonda Rossiyaga eksport qiluvchi korxonalar uchun ahamiyatli. "
        "2016-yildan joriy.",
    ),
    (
        "GOST 12.0.001-82",
        "Система стандартов безопасности труда — Основные положения (Mehnat xavfsizligi standartlari tizimi — Asosiy qoidalar)",
        "1982/2004",
        "Ko'p soha (universal)",
        "SSBT — Mehnat xavfsizligi standartlari tizimining asosiy standarti. "
        "1982-yilda qabul qilingan, hali kuchda. O'zbekistonda ham qo'llaniladi. "
        "Barcha sanoat tarmoqlarida mehnat xavfsizligini tartibga soluvchi asosiy hujjat. "
        "CIS davlatlarida OHSAS/ISO 45001 bilan parallel qo'llaniladi.",
    ),
    (
        "GOST 12.1.003-2014",
        "Система стандартов безопасности труда — Шум — Общие требования безопасности (Shovqin — Xavfsizlikka umumiy talablar)",
        "2014",
        "Ko'p soha (universal)",
        "Ishlab chiqarishdagi shovqin darajasiga qo'yiladigan xavfsizlik talablari. "
        "Sanoat korxonalarida shovqin normalarini belgilaydi. "
        "O'zbekiston mehnat xavfsizligi nazoratida qo'llaniladi. "
        "ILO konventsiyalari bilan mos.",
    ),
    (
        "GOST 34.10-2018",
        "Информационная технология — Криптографическая защита информации — Процессы формирования и проверки электронной цифровой подписи",
        "2018",
        "Axborot texnologiyalari",
        "Elektron raqamli imzo shakllantirish va tekshirish jarayonlari standarti. "
        "CIS davlatlarida ERI (Elektron raqamli imzo) tizimlarida qo'llaniladi. "
        "O'zbekistonda e-hukumat va elektron hujjat aylanmasi uchun muhim. "
        "Kriptografik himoya standarti.",
    ),
    (
        "GOST R 52166-2003",
        "Плодоовощная продукция — Определение остаточных количеств пестицидов (Sabzavot va mevalar — Pestitsid qoldiqlarini aniqlash)",
        "2003",
        "Qishloq xo'jaligi",
        "Sabzavot va mevalarda pestitsid qoldiq miqdorini aniqlash usullari. "
        "CIS davlatlarida qishloq xo'jaligi mahsulotlari eksportida qo'llaniladi. "
        "O'zbekistonda meva-sabzavot eksportini nazorat qilishda muhim. "
        "SanPiN talablari bilan bog'liq.",
    ),
    (
        "GOST 26929-94",
        "Сырье и продукты пищевые — Подготовка проб — Минерализация для определения содержания токсичных элементов",
        "1994",
        "Oziq-ovqat",
        "Oziq-ovqat xomashyosi va mahsulotlarida toksik elementlarni aniqlash uchun namuna tayyorlash. "
        "CIS oziq-ovqat laboratoriyalarida keng qo'llaniladigan standart. "
        "O'zbekistonda oziq-ovqat xavfsizligi nazoratida qo'llaniladi.",
    ),
    (
        "GOST 9.304-87",
        "Единая система защиты от коррозии и старения — Покрытия металлические и неметаллические неорганические",
        "1987",
        "Mashinasozlik",
        "Korroziyadan va eskirishdan himoya tizimi — metall va noorganik qoplamalar standarti. "
        "O'zbekiston mashinasozlik va metallurgiya sanoatida keng qo'llaniladi. "
        "Alyuminiy, sink, xrom va boshqa qoplamalar uchun talablar.",
    ),
    (
        "GOST 7.1-2003",
        "Система стандартов по информации, библиотечному и издательскому делу — Библиографическая запись",
        "2003",
        "Ko'p soha (universal)",
        "Bibliografik yozuv standarti. Kitoblar, maqolalar va boshqa nashrlar uchun. "
        "O'zbekiston kutubxona va nashriyot sohasida qo'llaniladi. "
        "SIBID tizimining asosi.",
    ),
    (
        "GOST 8.417-2002",
        "Государственная система обеспечения единства измерений — Единицы величин",
        "2002",
        "Ko'p soha (universal)",
        "O'lchov birliklari davlat tizimi — kattaliklarning birliklari. "
        "SI tizimiga asoslangan CIS davlatlari uchun metrologiya standarti. "
        "O'zbekistonda Metrologiya qonunchiligi bilan bog'liq. "
        "Barcha texnik hujjatlarda qo'llaniladigan asosiy standart.",
    ),
    (
        "GOST 30244-94",
        "Материалы строительные — Методы испытаний на горючесть (Qurilish materiallari — Yonuvchanlikni sinash usullari)",
        "1994",
        "Qurilish",
        "Qurilish materiallarining yonuvchanligini aniqlash usullari. "
        "O'zbekiston qurilish sohasida yong'in xavfsizligi nazoratida qo'llaniladi. "
        "Binolar qurilishida materiallar tanlashda majburiy sinovlar.",
    ),
    (
        "GOST ISO 6945-93",
        "Хлопок-волокно — Определение линейной плотности — Метод взвешивания (Paxta tolasi — Chiziqli zichligini aniqlash)",
        "1993",
        "To'qimachilik",
        "Paxta tolasining chiziqli zichligini (nomer/tex) aniqlash usuli. "
        "O'zbekiston to'qimachilik sanoatida keng qo'llaniladi. "
        "Paxta eksporti sifat nazoratida muhim. "
        "ISO 6945:1990 asosida CIS uchun moslashtirilgan.",
    ),
    (
        "GOST R 56020-2014",
        "Бережливое производство — Основные положения и словарь (Tejamkor ishlab chiqarish — Asosiy qoidalar va lug'at)",
        "2014",
        "Ko'p soha (universal)",
        "Lean Production (Tejamkor ishlab chiqarish) — asosiy qoidalar va terminologiya. "
        "Toyota ishlab chiqarish tizimi (TPS) tamoyillariga asoslangan. "
        "Rossiya sanoatida keng joriy etilmoqda; O'zbekiston korxonalarida qo'llanila boshlandi. "
        "Isrofgarchilikni kamaytirish va samaradorlikni oshirish.",
    ),
    (
        "GOST 2.105-2019",
        "Единая система конструкторской документации — Общие требования к текстовым документам",
        "2019",
        "Mashinasozlik",
        "Konstruktorlik hujjatlari yagona tizimi — matnli hujjatlarga umumiy talablar. "
        "O'zbekiston mashinasozlik, asbobsozlik va muhandislik sohasida keng qo'llaniladi. "
        "Loyihalar va texnik hujjatlar uchun majburiy format.",
    ),
    (
        "GOST R ISO 22000-2019",
        "Системы менеджмента безопасности пищевой продукции — Требования к организациям, участвующим в цепи создания пищевой продукции",
        "2019",
        "Oziq-ovqat",
        "ISO 22000:2018 ning Rossiya milliy versiyasi (GOST R). "
        "O'zbekistonda Rossiyaga oziq-ovqat eksport qiluvchi korxonalar uchun muhim. "
        "HACCP tamoyillari bilan birga qo'llaniladi. "
        "Oziq-ovqat zanjirining barcha ishtirokchilari uchun.",
    ),
]


def get_or_create_industry(name):
    """Sanoatni topadi yoki yaratadi."""
    obj, _ = Industry.objects.get_or_create(
        name=name,
        defaults={'is_active': True, 'order': 99},
    )
    return obj


class Command(BaseCommand):
    help = 'ISO, UzDST va GOST standartlar bazasini yuklaydi (rasmiy manbalar asosida)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--type',
            choices=['iso', 'uzdst', 'gost', 'all'],
            default='all',
            help='Qaysi standartlarni yuklash: iso | uzdst | gost | all',
        )

    def handle(self, *args, **options):
        target = options['type']
        total_created = 0
        total_updated = 0

        datasets = []
        if target in ('iso', 'all'):
            datasets.append(('ISO', 'international', ISO_STANDARDS))
        if target in ('uzdst', 'all'):
            datasets.append(('UzDST', 'local', UZDST_STANDARDS))
        if target in ('gost', 'all'):
            datasets.append(('GOST', 'local', GOST_STANDARDS))

        for label, std_type, standards in datasets:
            self.stdout.write(f'\n── {label} standartlari ──────────────────────────────')
            created = updated = 0

            for code, name, version, industry_name, description in standards:
                industry = get_or_create_industry(industry_name)
                obj, was_created = Standard.objects.get_or_create(
                    code=code,
                    defaults={
                        'name': name,
                        'type': std_type,
                        'version': version,
                        'industry': industry,
                        'description': description,
                        'is_active': True,
                    },
                )
                if was_created:
                    created += 1
                    self.stdout.write(f'  ✓ {code}')
                else:
                    # Mavjud bo'lsa ham ma'lumotni yangilash
                    changed = False
                    if obj.name != name:
                        obj.name = name
                        changed = True
                    if obj.description != description:
                        obj.description = description
                        changed = True
                    if obj.version != version:
                        obj.version = version
                        changed = True
                    if changed:
                        obj.save()
                        updated += 1
                        self.stdout.write(f'  ↻ {code} (yangilandi)')
                    else:
                        self.stdout.write(f'  · {code} (mavjud)')

            self.stdout.write(
                self.style.SUCCESS(
                    f'  {label}: {created} yangi, {updated} yangilandi'
                )
            )
            total_created += created
            total_updated += updated

        self.stdout.write(
            self.style.SUCCESS(
                f'\n✅ Jami: {total_created} ta yangi standart qo\'shildi, '
                f'{total_updated} ta yangilandi.'
            )
        )
        self.stdout.write(
            f'   ISO: {len(ISO_STANDARDS)} | UzDST: {len(UZDST_STANDARDS)} | GOST: {len(GOST_STANDARDS)}'
        )
