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
# Format: (code, name_uz, name_ru, name_en, version, industry, desc_uz, desc_ru, desc_en)
ISO_STANDARDS = [
    (
        "ISO 9001:2015",
        "Sifat menejmenti tizimlari — Talablar",
        "Системы менеджмента качества — Требования",
        "Quality management systems — Requirements",
        "2015", "Ko'p soha (universal)",
        "Sifat menejmenti tizimiga qo'yiladigan talablar. Har qanday soha va o'lchamdagi tashkilotlarga tatbiq etiladi. Dunyo bo'ylab 1 milliondan ortiq tashkilot sertifikatga ega. PDCA tsikliga asoslangan. Asosiy e'tibor: risklarga asoslangan fikrlash, mijoz talablarini qondirish.",
        "Требования к системам менеджмента качества. Применяется к организациям любого размера и отрасли. Более 1 миллиона сертифицированных организаций в мире. Основан на цикле PDCA. Ключевой принцип: риск-ориентированное мышление и удовлетворение требований потребителей.",
        "Requirements for quality management systems applicable to any organization regardless of size or sector. Over 1 million certified organizations worldwide. Based on the PDCA cycle. Key focus: risk-based thinking and meeting customer requirements.",
    ),
    (
        "ISO 14001:2015",
        "Atrof-muhit menejmenti tizimlari — Talablar va qo'llash bo'yicha ko'rsatmalar",
        "Системы экологического менеджмента — Требования и руководство по применению",
        "Environmental management systems — Requirements with guidance for use",
        "2015", "Ko'p soha (universal)",
        "Atrof-muhit menejmenti tizimiga qo'yiladigan talablar. Tashkilotlarga atrof-muhitga salbiy ta'sirni kamaytirish va ekologik samaradorlikni oshirishda yordam beradi. 2015-yil nashrida ISO Annex SL tuzilmasiga moslashtirilgan. 300 000+ sertifikatlangan tashkilot.",
        "Требования к системам экологического менеджмента. Помогает снизить негативное воздействие на окружающую среду и повысить экологические показатели. Редакция 2015 года приведена в соответствие со структурой Annex SL. Более 300 000 сертифицированных организаций.",
        "Requirements for environmental management systems. Helps organizations reduce negative environmental impact and improve environmental performance. 2015 edition aligned with ISO Annex SL high-level structure. 300,000+ certified organizations worldwide.",
    ),
    (
        "ISO 45001:2018",
        "Mehnat xavfsizligi va sog'liqni saqlash menejmenti tizimlari — Talablar va qo'llash bo'yicha ko'rsatmalar",
        "Системы менеджмента охраны здоровья и безопасности труда — Требования и руководство по применению",
        "Occupational health and safety management systems — Requirements with guidance for use",
        "2018", "Ko'p soha (universal)",
        "Mehnat xavfsizligi va sog'liqni saqlash menejmenti tizimi talablari. 2018-yil 12-martda nashr etilgan. OHSAS 18001 o'rnini bosgan (3 yillik o'tish davri). Maqsad: ishchilarni mehnat jarohatlaridan va kasb xastaliklari xavfidan himoya qilish. 70+ mamlakatda milliy standart sifatida qabul qilingan.",
        "Требования к системам менеджмента охраны здоровья и безопасности труда. Опубликован 12 марта 2018 года, заменил OHSAS 18001. Цель: защита работников от производственных травм и профессиональных заболеваний. Принят национальным стандартом в 70+ странах.",
        "Requirements for occupational health and safety management systems. Published March 12, 2018, replacing OHSAS 18001. Aims to protect workers from work-related injuries and occupational diseases. Adopted as national standard in 70+ countries.",
    ),
    (
        "ISO 22000:2018",
        "Oziq-ovqat xavfsizligi menejmenti tizimlari — Oziq-ovqat zanjirining har qanday tashkilotiga talablar",
        "Системы менеджмента безопасности пищевой продукции — Требования к организациям пищевой цепи",
        "Food safety management systems — Requirements for any organization in the food chain",
        "2018", "Oziq-ovqat",
        "Oziq-ovqat xavfsizligi menejmenti tizimiga qo'yiladigan talablar. Oziq-ovqat zanjirining har qanday bo'g'inidagi tashkilotlarga tatbiq etiladi. HACCP tamoyillarini o'z ichiga oladi. 2018-yil nashrida Annex SL bilan moslashtirilgan. 51 535 ta sertifikatlangan sayt (ISO Survey 2022).",
        "Требования к системам менеджмента безопасности пищевой продукции. Применяется к любой организации в пищевой цепочке. Включает принципы ХАССП. Редакция 2018 года приведена в соответствие с Annex SL. 51 535 сертифицированных объектов (ISO Survey 2022).",
        "Requirements for food safety management systems for any organization in the food chain. Incorporates HACCP principles. 2018 edition aligned with Annex SL. 51,535 certified sites (ISO Survey 2022). First published in 2005.",
    ),
    (
        "ISO/IEC 27001:2022",
        "Axborot xavfsizligi, kiberxavfsizlik va maxfiylikni himoya qilish — Axborot xavfsizligi menejmenti tizimlari — Talablar",
        "Информационная безопасность, кибербезопасность и защита конфиденциальности — Системы менеджмента информационной безопасности — Требования",
        "Information security, cybersecurity and privacy protection — Information security management systems — Requirements",
        "2022", "Axborot texnologiyalari",
        "Axborot xavfsizligi menejmenti tizimiga qo'yiladigan talablar. Dastlab 2005-yilda nashr etilgan (BS 7799 asosida), 2013 va 2022-yilda yangilangan. 10 ta asosiy bo'lim + Annex A (93 ta xavfsizlik nazorat vositasi). Sertifikatlash uchun tashqi audit: 2 bosqich + davriy tekshiruv.",
        "Требования к системам менеджмента информационной безопасности. Первоначально опубликован в 2005 году (на основе BS 7799), обновлён в 2013 и 2022 годах. 10 основных разделов + Приложение A (93 средства управления). Сертификация: двухэтапный аудит и периодические проверки.",
        "Requirements for information security management systems. Originally published 2005 (based on BS 7799), updated 2013 and 2022. 10 main clauses + Annex A with 93 security controls. Certification requires a two-stage external audit plus periodic surveillance.",
    ),
    (
        "ISO 50001:2018",
        "Energiya menejmenti tizimlari — Talablar va qo'llash bo'yicha ko'rsatmalar",
        "Системы энергетического менеджмента — Требования и руководство по применению",
        "Energy management systems — Requirements with guidance for use",
        "2018", "Elektrotexnika",
        "Energiya menejmenti tizimiga qo'yiladigan talablar. Energiya sarfini tizimli ravishda kamaytirish va energiya samaradorligini oshirish maqsadida. Birinchi nashr: 2011-yil; ikkinchi nashr: 2018-yil. PDCA tsikliga asoslangan. Sanoat korxonalari va kommunal xizmatlar uchun.",
        "Требования к системам энергетического менеджмента для систематического снижения потребления энергии. Первое издание: 2011 год; второе: 2018 год. Основан на цикле PDCA. Для промышленных предприятий и коммунальных служб.",
        "Requirements for energy management systems to systematically reduce energy consumption and improve efficiency. First edition 2011; second edition 2018. Based on PDCA cycle. For industrial enterprises and utilities.",
    ),
    (
        "ISO 13485:2016",
        "Tibbiy qurilmalar — Sifat menejmenti tizimlari — Tartibga solish maqsadlari uchun talablar",
        "Изделия медицинские — Системы менеджмента качества — Требования для целей регулирования",
        "Medical devices — Quality management systems — Requirements for regulatory purposes",
        "2016", "Tibbiyot",
        "Tibbiy qurilmalar sifat menejmenti tizimiga qo'yiladigan talablar. 1996-yilda birinchi marta nashr etilgan; joriy versiya 2016-yil 1-martda. ISO 9001 dan farqi: doimiy takomillashtirish emas, samarali amalga oshirishni talab qiladi. FDA 21 CFR 820 va Yevropa MDR talablari bilan moslashtirilgan.",
        "Требования к системам менеджмента качества медицинских изделий. Первое издание: 1996 год; действующая версия от 1 марта 2016 года. В отличие от ISO 9001 требует эффективного внедрения, а не непрерывного улучшения. Согласован с FDA 21 CFR 820 и европейским MDR.",
        "Requirements for quality management systems for medical devices. First published 1996; current version March 1, 2016. Unlike ISO 9001, requires effective implementation rather than continual improvement. Aligned with FDA 21 CFR 820 and European MDR.",
    ),
    (
        "ISO 31000:2018",
        "Risk menejmenti — Ko'rsatmalar",
        "Менеджмент рисков — Руководящие указания",
        "Risk management — Guidelines",
        "2018", "Neft va gaz",
        "Risk menejmenti bo'yicha ko'rsatmalar. 2009-yilda birinchi marta nashr etilgan, 2018-yilda qayta ko'rib chiqilgan (8 ta tamoyilga qisqartirilgan). 82 mamlakatda milliy standart sifatida qabul qilingan. Sertifikatlash uchun emas — tatbiq etish uchun.",
        "Руководство по менеджменту рисков. Первое издание — 2009 год, пересмотрено в 2018 году (сокращено до 8 принципов). Принято в 82 странах как национальный стандарт. Носит рекомендательный характер, не предназначен для сертификации.",
        "Guidelines for risk management. First published 2009, revised 2018 (condensed to 8 principles). Adopted as national standard in 82 countries. A guideline document — not intended for third-party certification.",
    ),
    (
        "ISO 22301:2019",
        "Xavfsizlik va barqarorlik — Biznes uzluksizligi menejmenti tizimlari — Talablar",
        "Безопасность и устойчивость — Системы менеджмента непрерывности деятельности — Требования",
        "Security and resilience — Business continuity management systems — Requirements",
        "2019", "Axborot texnologiyalari",
        "Biznes uzluksizligi menejmenti tizimiga qo'yiladigan talablar. Tashkilotlarga falokatlar va boshqa inqirozlarda faoliyatni davom ettirish imkonini beradi. 2019-yilda ISO/IEC 27001 bilan moslashtirilgan. Birinchi nashr: 2012-yil (BS 25999 o'rnini bosgan).",
        "Требования к системам менеджмента непрерывности деятельности. Позволяет организациям работать в условиях катастроф и кризисов. В 2019 году приведён в соответствие с ISO/IEC 27001. Первое издание: 2012 год (заменил BS 25999).",
        "Requirements for business continuity management systems. Enables organizations to continue operations during disasters and crises. Updated in 2019 to align with ISO/IEC 27001. First published 2012, replacing BS 25999.",
    ),
    (
        "ISO 26000:2010",
        "Ijtimoiy mas'uliyat bo'yicha ko'rsatmalar",
        "Руководство по социальной ответственности",
        "Guidance on social responsibility",
        "2010", "Qishloq xo'jaligi",
        "Ijtimoiy mas'uliyat bo'yicha ko'rsatmalar. 2010-yildan beri o'zgarmagan. Sertifikatlash uchun emas — tatbiq etish uchun. 7 ta asosiy mavzu: tashkiliy boshqaruv, inson huquqlari, mehnat amaliyoti, atrof-muhit, adolatli biznes amaliyoti, iste'molchi masalalari, jamiyat ishtiroki.",
        "Руководство по социальной ответственности организаций. Не менялось с 2010 года. Не предназначено для сертификации. 7 основных тем: организационное управление, права человека, трудовые практики, окружающая среда, добросовестные деловые практики, интересы потребителей, развитие сообщества.",
        "Guidance on social responsibility for organizations. Unchanged since 2010. Not intended for certification. 7 core subjects: organizational governance, human rights, labour practices, the environment, fair operating practices, consumer issues, and community involvement.",
    ),
    (
        "ISO 37001:2016",
        "Korrupsiyaga qarshi menejmenti tizimlari — Talablar va qo'llash bo'yicha ko'rsatmalar",
        "Системы менеджмента противодействия взяточничеству — Требования и руководство по применению",
        "Anti-bribery management systems — Requirements with guidance for use",
        "2016", "Neft va gaz",
        "Korrupsiyaga qarshi menejmenti tizimiga qo'yiladigan talablar. 2016-yil 15-oktabrda birinchi marta nashr etilgan. Tashkilotlarga pora berish va olishning oldini olish tizimini joriy etishda yordam beradi. FCPA (AQSh) va UK Bribery Act talablariga mos.",
        "Требования к системам менеджмента противодействия взяточничеству. Опубликован 15 октября 2016 года. Помогает организациям внедрять системы предотвращения взяточничества. Соответствует FCPA (США) и UK Bribery Act.",
        "Requirements for anti-bribery management systems. Published October 15, 2016. Helps organizations implement systems to prevent, detect, and address bribery. Aligned with FCPA (USA) and UK Bribery Act requirements.",
    ),
    (
        "ISO/IEC 20000-1:2018",
        "Axborot texnologiyalari — Xizmatlarni boshqarish — 1-qism: Xizmatlarni boshqarish tizimiga talablar",
        "Информационные технологии — Управление услугами — Часть 1: Требования к системе управления услугами",
        "Information technology — Service management — Part 1: Service management system requirements",
        "2018", "Axborot texnologiyalari",
        "IT xizmatlarini boshqarish tizimiga qo'yiladigan talablar. 2005-yilda birinchi marta nashr etilgan (BS 15000 asosida). ITIL amaliyotlari bilan chambarchas bog'liq. 2018-yil nashrida Annex SL tuzilmasiga moslashtirilgan.",
        "Требования к системам управления IT-услугами. Первое издание: 2005 год (на основе BS 15000). Тесно связан с практиками ITIL. Редакция 2018 года приведена в соответствие со структурой Annex SL. Для поставщиков IT-услуг.",
        "Requirements for IT service management systems. First published 2005 (based on BS 15000). Closely aligned with ITIL practices. 2018 edition aligned with Annex SL structure. For IT service providers.",
    ),
    (
        "ISO/IEC 17025:2017",
        "Sinov va kalibrlash laboratoriyalari kompetentligiga umumiy talablar",
        "Общие требования к компетентности испытательных и калибровочных лабораторий",
        "General requirements for the competence of testing and calibration laboratories",
        "2017", "Kimyo",
        "Sinov va kalibrlash laboratoriyalari kompetentligiga umumiy talablar. 1999-yilda birinchi marta nashr etilgan; 2005 va 2017-yillarda yangilangan. Akkreditatsiya organlari (ILAC a'zolari) tomonidan tatbiq etiladi. ISO 9001 bilan mos, lekin laboratoriyaga xos qo'shimcha talablar mavjud.",
        "Общие требования к компетентности испытательных и калибровочных лабораторий. Первое издание: 1999 год; обновлено в 2005 и 2017 годах. Применяется органами по аккредитации — членами ILAC. Совместим с ISO 9001, но содержит специфические требования для лабораторий.",
        "General requirements for competence of testing and calibration laboratories. First published 1999; updated 2005 and 2017. Applied by accreditation bodies (ILAC members). Compatible with ISO 9001 but with additional laboratory-specific requirements.",
    ),
    (
        "ISO 15189:2022",
        "Tibbiy laboratoriyalar — Sifat va kompetentlikka talablar",
        "Медицинские лаборатории — Требования к качеству и компетентности",
        "Medical laboratories — Requirements for quality and competence",
        "2022", "Tibbiyot",
        "Tibbiy laboratoriyalar sifati va kompetentligiga qo'yiladigan talablar. ISO/IEC 17025 asosida, lekin tibbiy laboratoriya xususiyatlariga moslashtirilgan. 2003-yilda birinchi marta nashr etilgan; 2012 va 2022-yillarda yangilangan. Klinik laboratoriyalar akkreditatsiyasi uchun asosiy standart.",
        "Требования к качеству и компетентности медицинских лабораторий. Основан на ISO/IEC 17025, адаптирован для медицинских лабораторий. Первое издание: 2003 год; обновлено в 2012 и 2022 годах. Основной стандарт для аккредитации клинических лабораторий.",
        "Requirements for quality and competence in medical laboratories. Based on ISO/IEC 17025 but adapted for medical laboratory specifics. First published 2003; updated 2012 and 2022. The primary standard for clinical laboratory accreditation.",
    ),
    (
        "ISO 28000:2022",
        "Xavfsizlik va barqarorlik — Xavfsizlik menejmenti tizimlari — Talablar",
        "Безопасность и устойчивость — Системы менеджмента безопасности — Требования",
        "Security and resilience — Security management systems — Requirements",
        "2022", "Mashinasozlik",
        "Ta'minot zanjiri xavfsizligi menejmenti tizimiga qo'yiladigan talablar. 2007-yilda birinchi marta nashr etilgan; 2022-yilda kengaytirilgan (faqat ta'minot zanjiri emas, umumiy xavfsizlik). Port operatorlari, logistika kompaniyalari, savdo tashkilotlari uchun.",
        "Требования к системам менеджмента безопасности. Первое издание: 2007 год; расширено в 2022 году (охватывает не только цепочку поставок, но и общую безопасность). Для операторов портов, логистических компаний и торговых организаций.",
        "Requirements for security management systems. First published 2007; expanded in 2022 beyond supply chains to general security. Designed for port operators, logistics companies, and trade organizations.",
    ),
]


# ─── UzDST STANDARTLARI (15 ta) ──────────────────────────────────────────────
# Format: (code, name_uz, name_ru, name_en, version, industry, desc_uz, desc_ru, desc_en)
UZDST_STANDARDS = [
    (
        "O'z DSt ISO 9001:2015",
        "Sifat menejmenti tizimlari — Talablar",
        "Системы менеджмента качества — Требования",
        "Quality management systems — Requirements",
        "2015", "Ko'p soha (universal)",
        "ISO 9001:2015 ning O'zbekiston milliy standarti sifatida qabul qilingan versiyasi. O'zbekistonda sertifikatlash uchun asosiy standart. Barcha soha va o'lchamdagi korxonalarga tatbiq etiladi. O'zbekiston Standartlashtirish agentligi tomonidan tasdiqlangan.",
        "Национальная версия ISO 9001:2015, принятая в Узбекистане. Основной стандарт для сертификации систем менеджмента качества в Узбекистане. Применяется к организациям всех отраслей и размеров. Утверждён Агентством по стандартизации Узбекистана.",
        "Uzbek national standard version of ISO 9001:2015. The primary quality management certification standard in Uzbekistan. Applicable to organizations of all sizes and sectors. Approved by the Uzbekistan Agency for Standardization.",
    ),
    (
        "O'z DSt ISO 14001:2015",
        "Atrof-muhit menejmenti tizimlari — Talablar va qo'llash bo'yicha ko'rsatmalar",
        "Системы экологического менеджмента — Требования и руководство по применению",
        "Environmental management systems — Requirements with guidance for use",
        "2015", "Ko'p soha (universal)",
        "ISO 14001:2015 ning O'zbekiston milliy versiyasi. Korxonalarning atrof-muhitga ta'sirini boshqarish tizimi. O'zbekistonda ekologik sertifikatlashning asosi. Ekologiya nazorati qonunchiligi talablari bilan bog'liq.",
        "Национальная версия ISO 14001:2015 в Узбекистане. Система управления воздействием предприятий на окружающую среду. Основа для экологической сертификации в Узбекистане. Связан с требованиями экологического законодательства страны.",
        "Uzbek national version of ISO 14001:2015. Environmental management system for organizations. Foundation for environmental certification in Uzbekistan. Linked to Uzbekistan's environmental legislation requirements.",
    ),
    (
        "O'z DSt ISO 22000:2018",
        "Oziq-ovqat xavfsizligi menejmenti tizimlari — Oziq-ovqat zanjirining har qanday tashkilotiga talablar",
        "Системы менеджмента безопасности пищевой продукции — Требования к организациям пищевой цепи",
        "Food safety management systems — Requirements for any organization in the food chain",
        "2018", "Oziq-ovqat",
        "ISO 22000:2018 ning O'zbekiston milliy versiyasi. Oziq-ovqat ishlab chiqaruvchilar, qayta ishlovchilar va distribyutorlar uchun. HACCP tamoyillarini o'z ichiga oladi. Eksportga mo'ljallangan oziq-ovqat mahsulotlari sertifikatlashda talab qilinadi.",
        "Национальная версия ISO 22000:2018 в Узбекистане. Для производителей, переработчиков и дистрибьюторов пищевой продукции. Включает принципы ХАССП. Требуется при сертификации продуктов питания для экспорта.",
        "Uzbek national version of ISO 22000:2018. For food producers, processors, and distributors. Incorporates HACCP principles. Required for certification of food products intended for export.",
    ),
    (
        "O'z DSt ISO 45001:2018",
        "Mehnat xavfsizligi va sog'liqni saqlash menejmenti tizimlari — Talablar va qo'llash bo'yicha ko'rsatmalar",
        "Системы менеджмента охраны здоровья и безопасности труда — Требования и руководство по применению",
        "Occupational health and safety management systems — Requirements with guidance for use",
        "2018", "Ko'p soha (universal)",
        "ISO 45001:2018 ning O'zbekiston milliy versiyasi. Mehnat muhofazasi va xavfsizligini ta'minlash tizimi. O'zbekiston Mehnat kodeksi va xavfsizlik qonunchiligi talablari bilan uyg'unlashtirilgan. Sanoat korxonalari uchun majburiy nazorat elementi.",
        "Национальная версия ISO 45001:2018 в Узбекистане. Система обеспечения охраны труда и техники безопасности. Согласована с Трудовым кодексом Узбекистана. Обязательный элемент надзора для промышленных предприятий.",
        "Uzbek national version of ISO 45001:2018. Occupational health and safety management system. Aligned with Uzbekistan's Labour Code and safety legislation. A mandatory supervision element for industrial enterprises.",
    ),
    (
        "O'z DSt ISO 50001:2018",
        "Energiya menejmenti tizimlari — Talablar va qo'llash bo'yicha ko'rsatmalar",
        "Системы энергетического менеджмента — Требования и руководство по применению",
        "Energy management systems — Requirements with guidance for use",
        "2018", "Elektrotexnika",
        "ISO 50001:2018 ning O'zbekiston milliy versiyasi. O'zbekistonda energiya tejamkorligi dasturlari doirasida qo'llaniladi. Yirik sanoat korxonalari va kommunal xizmatlar uchun. Energiya samaradorligi bo'yicha O'zbekiston qonunchiligi bilan bog'liq.",
        "Национальная версия ISO 50001:2018 в Узбекистане. Применяется в рамках программ по энергоэффективности. Для крупных промышленных предприятий и коммунальных служб. Связан с законодательством Узбекистана об энергосбережении.",
        "Uzbek national version of ISO 50001:2018. Applied within national energy efficiency programs. For large industrial enterprises and utilities. Linked to Uzbekistan's energy conservation legislation.",
    ),
    (
        "O'z DSt ISO/IEC 27001:2022",
        "Axborot xavfsizligi, kiberxavfsizlik va maxfiylikni himoya qilish — Axborot xavfsizligi menejmenti tizimlari — Talablar",
        "Информационная безопасность, кибербезопасность и защита конфиденциальности — Системы менеджмента информационной безопасности — Требования",
        "Information security, cybersecurity and privacy protection — Information security management systems — Requirements",
        "2022", "Axborot texnologiyalari",
        "ISO/IEC 27001:2022 ning O'zbekiston milliy versiyasi. O'zbekistonda raqamli iqtisodiyot va kiberxavfsizlik rivojlanishi bilan dolzarblashgan. Axborot xavfsizligi bo'yicha O'zbekiston qonunchiligi ('Axborotlashtirish to'g'risida' qonun) bilan bog'liq.",
        "Национальная версия ISO/IEC 27001:2022 в Узбекистане. Актуален в связи с развитием цифровой экономики и кибербезопасности в стране. Связан с законодательством Узбекистана об информационных технологиях.",
        "Uzbek national version of ISO/IEC 27001:2022. Highly relevant given Uzbekistan's digital economy and cybersecurity development. Linked to Uzbekistan's IT legislation on informatization.",
    ),
    (
        "O'z DSt 687:2021",
        "Iste'mol tovarlarining sifatini baholash — Umumiy talablar",
        "Оценка качества потребительских товаров — Общие требования",
        "Consumer goods quality assessment — General requirements",
        "2021", "To'qimachilik",
        "O'zbekistonda iste'mol tovarlarining sifatini baholashga qo'yiladigan umumiy talablar. Mahalliy ishlab chiqaruvchilar uchun sifat nazoratining asosi. Iste'molchilarni himoya qilish qonunchiligi bilan bog'liq. O'zbekiston milliy standarti.",
        "Общие требования к оценке качества потребительских товаров в Узбекистане. Основа контроля качества для отечественных производителей. Связан с законодательством о защите прав потребителей.",
        "General requirements for consumer goods quality assessment in Uzbekistan. Foundation for quality control for domestic manufacturers. Linked to consumer protection legislation. Uzbek national standard.",
    ),
    (
        "O'z DSt 1340:2019",
        "To'qimachilik materiallari — Sifat ko'rsatkichlari va sinov usullari",
        "Материалы текстильные — Показатели качества и методы испытания",
        "Textile materials — Quality indicators and test methods",
        "2019", "To'qimachilik",
        "O'zbekiston to'qimachilik sanoati uchun milliy standart. Paxta tolasi va to'qimachilik mahsulotlari sifatini baholash usullari. Eksport uchun to'qimachilik mahsulotlarini sertifikatlashda qo'llaniladi.",
        "Узбекский национальный стандарт для текстильной промышленности. Методы оценки качества хлопкового волокна и текстильных изделий. Применяется при сертификации текстильной продукции для экспорта.",
        "Uzbek national standard for the textile industry. Methods for assessing quality of cotton fibre and textile products. Applied when certifying textile goods for export.",
    ),
    (
        "O'z DSt ISO 22716:2014",
        "Kosmetika mahsulotlari — Yaxshi ishlab chiqarish amaliyoti (GMP) — Ko'rsatmalar",
        "Косметическая продукция — Надлежащая производственная практика (GMP) — Руководство",
        "Cosmetics — Good Manufacturing Practices (GMP) — Guidelines",
        "2014", "Farmatsevtika",
        "Kosmetika mahsulotlari ishlab chiqarishda yaxshi amaliyot ko'rsatmalari. ISO 22716:2007 asosida O'zbekistonda qabul qilingan. Kosmetika eksporteri va ishlab chiqaruvchilari uchun. Sanitariya nazorati qonunchiligi bilan bog'liq.",
        "Руководство по надлежащей производственной практике для косметической продукции. Принято в Узбекистане на основе ISO 22716:2007. Для производителей и экспортёров косметики. Связан с требованиями санитарного надзора.",
        "Guidelines for good manufacturing practices for cosmetic products. Adopted in Uzbekistan based on ISO 22716:2007. For cosmetics producers and exporters. Linked to sanitary control requirements.",
    ),
    (
        "O'z DSt ISO 17100:2016",
        "Tarjima xizmatlari — Tarjima xizmatlariga talablar",
        "Услуги по переводу — Требования к услугам перевода",
        "Translation services — Requirements for translation services",
        "2016", "Axborot texnologiyalari",
        "Tarjima xizmatlarining sifatiga qo'yiladigan talablar. O'zbekistonda ko'p tillilik (o'zbek, rus, ingliz) kontekstida muhim. Hukumat va tijorat hujjatlar tarjimasida qo'llaniladi.",
        "Требования к качеству услуг перевода. Актуален в контексте многоязычия в Узбекистане (узбекский, русский, английский). Применяется при переводе государственных и коммерческих документов.",
        "Requirements for the quality of translation services. Highly relevant in Uzbekistan's multilingual context (Uzbek, Russian, English). Applied for translating government and commercial documents.",
    ),
    (
        "O'z DSt ISO 3834-2:2021",
        "Metallar eritib payvandlash sifat talablari — 2-qism: To'liq sifat talablari",
        "Требования к качеству сварки плавлением металлических материалов — Часть 2: Всесторонние требования к качеству",
        "Quality requirements for fusion welding of metallic materials — Part 2: Comprehensive quality requirements",
        "2021", "Mashinasozlik",
        "Payvandlash jarayonlarining sifatiga to'liq talablar. O'zbekiston mashinasozlik sanoati uchun muhim standart. ISO 3834-2:2021 asosida qabul qilingan. Temir yo'l, qurilish va sanoat konstruktsiyalari uchun.",
        "Всесторонние требования к качеству процессов сварки плавлением. Важный стандарт для машиностроительной промышленности Узбекистана. Принят на основе ISO 3834-2:2021. Применяется в производстве железнодорожного и промышленного оборудования.",
        "Comprehensive quality requirements for fusion welding processes. Important standard for Uzbekistan's machinery manufacturing industry. Adopted based on ISO 3834-2:2021. Applied in production of railway, construction, and industrial equipment.",
    ),
    (
        "O'z DSt 2389:2020",
        "Qurilish materiallari — Tsement — Texnik talablar",
        "Материалы строительные — Цемент — Технические требования",
        "Building materials — Cement — Technical requirements",
        "2020", "Qurilish",
        "Qurilishda ishlatiladigan tsement sifatiga qo'yiladigan texnik talablar. O'zbekiston qurilish sanoatining asosiy mahalliy standarti. Tsement ishlab chiqaruvchilar va qurilish kompaniyalari uchun. Davlat nazorati va sertifikatlash asosi.",
        "Технические требования к цементу, используемому в строительстве. Основной отечественный стандарт строительной промышленности Узбекистана. Для производителей цемента и строительных компаний. Основа государственного контроля и сертификации.",
        "Technical requirements for cement used in construction. The primary domestic standard for Uzbekistan's construction industry. For cement producers and construction companies. Basis for state oversight and certification.",
    ),
    (
        "O'z DSt ISO 22483:2020",
        "Turizm va tegishli xizmatlar — Mehmonxonalar — Xizmat ko'rsatish sifati talablari",
        "Туризм и смежные услуги — Гостиницы — Требования к обслуживанию",
        "Tourism and related services — Hotels — Service requirements",
        "2020", "Qishloq xo'jaligi",
        "Mehmonxona xizmatlarining sifatiga qo'yiladigan talablar. O'zbekistonda turizm sanoatining rivojlanishi bilan dolzarblashgan. ISO 22483:2020 asosida qabul qilingan. O'zbekiston turizm klassifikatsiya tizimi bilan bog'liq.",
        "Требования к качеству гостиничного обслуживания. Актуален с учётом развития туристической отрасли Узбекистана. Принят на основе ISO 22483:2020. Связан с системой классификации туризма Узбекистана.",
        "Requirements for quality of hotel services. Highly relevant given Uzbekistan's growing tourism industry. Adopted based on ISO 22483:2020. Linked to Uzbekistan's tourism classification system.",
    ),
    (
        "O'z DSt EN ISO 80000-1:2015",
        "Miqdorlar va birliklar — 1-qism: Umumiy qoidalar",
        "Величины и единицы — Часть 1: Общие положения",
        "Quantities and units — Part 1: General",
        "2015", "Kimyo",
        "O'lchov birliklari va miqdorlar belgilanishiga umumiy qoidalar. O'zbekistonda metrologiya tizimining asosi. Barcha texnik hujjatlar va ilmiy ishlar uchun majburiy. SI tizimiga asoslangan.",
        "Общие правила обозначения физических величин и единиц измерения. Основа системы метрологии Узбекистана. Обязателен для всех технических документов и научных работ. Основан на системе СИ.",
        "General rules for the notation of physical quantities and units of measurement. Foundation of Uzbekistan's metrology system. Mandatory for all technical documents and scientific work. Based on the SI system.",
    ),
    (
        "O'z DSt ISO/IEC 17021-1:2015",
        "Muvofiqlikni baholash — Menejmenti tizimlarini audit qilish va sertifikatlash organlari uchun talablar",
        "Оценка соответствия — Требования к органам, проводящим аудит и сертификацию систем менеджмента",
        "Conformity assessment — Requirements for bodies providing audit and certification of management systems",
        "2015", "Mashinasozlik",
        "Sertifikatlash organlari faoliyatiga qo'yiladigan talablar. O'zbekistonda sertifikatlash organlarining akkreditatsiyasi uchun asos. O'zAkk tomonidan qo'llaniladi. ISO 9001, 14001, 45001 sertifikatlashni amalga oshiruvchi organlar uchun.",
        "Требования к деятельности органов по сертификации систем менеджмента. Основа для аккредитации органов по сертификации в Узбекистане. Применяется UzAkk. Для органов, проводящих сертификацию по ISO 9001, 14001, 45001.",
        "Requirements for bodies providing audit and certification of management systems. Foundation for accreditation of certification bodies in Uzbekistan. Applied by UzAkk. For bodies performing ISO 9001, 14001, 45001 certification.",
    ),
]


# ─── GOST STANDARTLARI (15 ta) ────────────────────────────────────────────────
# Manba: GOST — Yevroosiyo Standartlashtirish Kengashi (EASC)
# gost.ru | docs.cntd.ru
# Format: (code, name_uz, name_ru, name_en, version, industry, desc_uz, desc_ru, desc_en)
GOST_STANDARDS = [
    (
        "GOST R ISO 9001-2015",
        "Sifat menejmenti tizimlari — Talablar",
        "Системы менеджмента качества — Требования",
        "Quality management systems — Requirements",
        "2015", "Ko'p soha (universal)",
        "ISO 9001:2015 ning Rossiya milliy standarti sifatida qabul qilingan versiyasi. CIS davlatlarida keng qo'llaniladigan sifat menejmenti standarti. O'zbekistonda Rossiya bilan hamkorlik qiluvchi korxonalar uchun muhim.",
        "Российская национальная версия ISO 9001:2015. Широко применяемый стандарт менеджмента качества в странах СНГ. Для предприятий Узбекистана, сотрудничающих с Россией. Утверждён Росстандартом.",
        "Russian national version of ISO 9001:2015. Widely used quality management standard in CIS countries. Relevant for Uzbekistan enterprises cooperating with Russia.",
    ),
    (
        "GOST R ISO 14001-2016",
        "Atrof-muhit menejmenti tizimlari — Talablar va qo'llash bo'yicha ko'rsatmalar",
        "Системы экологического менеджмента — Требования и руководство по применению",
        "Environmental management systems — Requirements with guidance for use",
        "2016", "Ko'p soha (universal)",
        "ISO 14001:2015 ning GOST tizimiga moslashtirilgan versiyasi. Rossiya va CIS davlatlarida ekologik sertifikatlash uchun. O'zbekistonda Rossiyaga eksport qiluvchi korxonalar uchun ahamiyatli. 2016-yildan joriy.",
        "Российская версия ISO 14001:2015 в системе ГОСТ. Для экологической сертификации в странах СНГ. Важен для предприятий Узбекистана, экспортирующих в Россию. Действует с 2016 года.",
        "Russian GOST version of ISO 14001:2015. For environmental certification in CIS countries. Relevant for Uzbekistan enterprises exporting to Russia. Effective since 2016.",
    ),
    (
        "GOST 12.0.001-82",
        "Mehnat xavfsizligi standartlari tizimi — Asosiy qoidalar",
        "Система стандартов безопасности труда — Основные положения",
        "System of occupational safety standards — Basic provisions",
        "1982/2004", "Ko'p soha (universal)",
        "SSBT — Mehnat xavfsizligi standartlari tizimining asosiy standarti. 1982-yilda qabul qilingan, hali kuchda. O'zbekistonda ham qo'llaniladi. Barcha sanoat tarmoqlarida mehnat xavfsizligini tartibga soluvchi asosiy hujjat.",
        "Основной стандарт системы стандартов безопасности труда (ССБТ). Принят в 1982 году, до сих пор действует. Применяется в Узбекистане. Регулирует охрану труда во всех отраслях промышленности.",
        "Foundational standard of the CIS occupational safety standards system (SSBT). Adopted 1982, still in force. Applied in Uzbekistan. Regulates occupational safety across all industrial sectors.",
    ),
    (
        "GOST 12.1.003-2014",
        "Mehnat xavfsizligi standartlari tizimi — Shovqin — Xavfsizlikka umumiy talablar",
        "Система стандартов безопасности труда — Шум — Общие требования безопасности",
        "System of occupational safety standards — Noise — General safety requirements",
        "2014", "Mashinasozlik",
        "Ishlab chiqarishdagi shovqin darajasiga qo'yiladigan xavfsizlik talablari. Sanoat korxonalarida shovqin normalarini belgilaydi. O'zbekiston mehnat xavfsizligi nazoratida qo'llaniladi. ILO konventsiyalari bilan mos.",
        "Требования безопасности к уровням шума на производстве. Устанавливает нормы шума для промышленных предприятий. Применяется в контроле охраны труда в Узбекистане. Соответствует конвенциям МОТ.",
        "Safety requirements for noise levels in production environments. Establishes noise standards for industrial enterprises. Applied in occupational safety control in Uzbekistan. Aligned with ILO conventions.",
    ),
    (
        "GOST 34.10-2018",
        "Axborot texnologiyalari — Axborotni kriptografik himoya qilish — Elektron raqamli imzoni shakllantirish va tekshirish jarayonlari",
        "Информационная технология — Криптографическая защита информации — Процессы формирования и проверки электронной цифровой подписи",
        "Information technology — Cryptographic information security — Processes of forming and verifying electronic digital signatures",
        "2018", "Axborot texnologiyalari",
        "Elektron raqamli imzo shakllantirish va tekshirish jarayonlari standarti. CIS davlatlarida ERI tizimlarida qo'llaniladi. O'zbekistonda e-hukumat va elektron hujjat aylanmasi uchun muhim.",
        "Стандарт процессов формирования и проверки электронной цифровой подписи. Применяется в системах ЭЦП в странах СНГ. Важен для электронного правительства и документооборота в Узбекистане.",
        "Standard for forming and verifying electronic digital signatures. Applied in EDS systems in CIS countries. Important for e-government and electronic document management in Uzbekistan.",
    ),
    (
        "GOST R 52166-2003",
        "Meva-sabzavot mahsulotlari — Pestitsid qoldiq miqdorini aniqlash",
        "Продукция плодоовощная — Определение остаточных количеств пестицидов",
        "Fruit and vegetable products — Determination of residual pesticide amounts",
        "2003", "Qishloq xo'jaligi",
        "Sabzavot va mevalarda pestitsid qoldiq miqdorini aniqlash usullari. CIS davlatlarida qishloq xo'jaligi mahsulotlari eksportida qo'llaniladi. O'zbekistonda meva-sabzavot eksportini nazorat qilishda muhim.",
        "Методы определения остаточных количеств пестицидов в плодовощной продукции. Применяется в экспортном контроле сельскохозяйственной продукции стран СНГ. Важен для экспорта плодоовощной продукции из Узбекистана.",
        "Methods for determining residual pesticide amounts in fruit and vegetable products. Applied in export quality control of agricultural goods in CIS countries. Important for Uzbekistan's fruit and vegetable exports.",
    ),
    (
        "GOST 26929-94",
        "Xomashyo va oziq-ovqat mahsulotlari — Namuna tayyorlash — Toksik elementlarni aniqlash uchun mineralizatsiya",
        "Сырьё и продукты пищевые — Подготовка проб — Минерализация для определения содержания токсичных элементов",
        "Raw materials and food products — Sample preparation — Mineralisation for determination of toxic elements",
        "1994", "Oziq-ovqat",
        "Oziq-ovqat xomashyosi va mahsulotlarida toksik elementlarni aniqlash uchun namuna tayyorlash. CIS oziq-ovqat laboratoriyalarida keng qo'llaniladigan standart. O'zbekistonda oziq-ovqat xavfsizligi nazoratida qo'llaniladi.",
        "Методы подготовки проб пищевого сырья для определения токсичных элементов. Широко применяется в лабораториях пищевой продукции СНГ. Используется в контроле безопасности пищевой продукции в Узбекистане.",
        "Methods for preparing food raw material samples to determine toxic element content. Widely applied in CIS food product laboratories. Used in food safety control in Uzbekistan.",
    ),
    (
        "GOST 9.304-87",
        "Korroziyadan va eskirishdan himoya yagona tizimi — Metall va noorganik qoplamalar",
        "Единая система защиты от коррозии и старения — Покрытия металлические и неметаллические неорганические",
        "Unified system of corrosion and ageing protection — Metal and non-metal inorganic coatings",
        "1987", "Mashinasozlik",
        "Korroziyadan va eskirishdan himoya tizimi — metall va noorganik qoplamalar standarti. O'zbekiston mashinasozlik va metallurgiya sanoatida keng qo'llaniladi. Alyuminiy, sink, xrom va boshqa qoplamalar uchun talablar.",
        "Стандарт на защитные металлические и неорганические покрытия от коррозии. Широко применяется в машиностроении и металлургии Узбекистана. Устанавливает требования к покрытиям из алюминия, цинка, хрома и других материалов.",
        "Standard for protective metal and inorganic coatings against corrosion. Widely applied in Uzbekistan's machinery manufacturing and metallurgy. Establishes requirements for aluminium, zinc, chrome, and other coatings.",
    ),
    (
        "GOST 7.1-2003",
        "Axborot, kutubxona va nashriyot ishlari standartlari tizimi — Bibliografik yozuv",
        "Система стандартов по информации, библиотечному и издательскому делу — Библиографическая запись",
        "System of standards on information, librarianship, and publishing — Bibliographic record",
        "2003", "Axborot texnologiyalari",
        "Bibliografik yozuv standarti. Kitoblar, maqolalar va boshqa nashrlar uchun. O'zbekiston kutubxona va nashriyot sohasida qo'llaniladi. SIBID tizimining asosi.",
        "Стандарт библиографических записей для книг, статей и других изданий. Применяется в библиотечном и издательском деле Узбекистана. Основа системы СИБИД.",
        "Standard for bibliographic records for books, articles, and other publications. Applied in Uzbekistan's library and publishing sectors. Forms the basis of the SIBID standards system.",
    ),
    (
        "GOST 8.417-2002",
        "O'lchov birligini ta'minlashning davlat tizimi — Kattaliklarning birliklari",
        "Государственная система обеспечения единства измерений — Единицы величин",
        "State system for ensuring the uniformity of measurements — Units of quantities",
        "2002", "Kimyo",
        "O'lchov birliklari davlat tizimi — kattaliklarning birliklari. SI tizimiga asoslangan CIS davlatlari uchun metrologiya standarti. O'zbekistonda Metrologiya qonunchiligi bilan bog'liq.",
        "Единицы физических величин в государственной системе обеспечения единства измерений. Основан на системе СИ. Связан с метрологическим законодательством Узбекистана. Обязателен для всех технических документов.",
        "Units of physical quantities in the state system for uniformity of measurements. Based on the SI system. Linked to Uzbekistan's metrology legislation. Mandatory for all technical documents.",
    ),
    (
        "GOST 30244-94",
        "Qurilish materiallari — Yonuvchanlikni sinash usullari",
        "Материалы строительные — Методы испытаний на горючесть",
        "Building materials — Flammability test methods",
        "1994", "Qurilish",
        "Qurilish materiallarining yonuvchanligini aniqlash usullari. O'zbekiston qurilish sohasida yong'in xavfsizligi nazoratida qo'llaniladi. Binolar qurilishida materiallar tanlashda majburiy sinovlar.",
        "Методы испытания строительных материалов на горючесть. Применяется в контроле пожарной безопасности строительства в Узбекистане. Обязательные испытания при выборе материалов для зданий.",
        "Methods for testing flammability of building materials. Applied in fire safety control in Uzbekistan's construction sector. Mandatory tests when selecting materials for building construction.",
    ),
    (
        "GOST ISO 6945-93",
        "Paxta tolasi — Chiziqli zichligini aniqlash — Tortish usuli",
        "Хлопок-волокно — Определение линейной плотности — Метод взвешивания",
        "Cotton fibre — Determination of linear density — Weighing method",
        "1993", "To'qimachilik",
        "Paxta tolasining chiziqli zichligini (nomer/tex) aniqlash usuli. O'zbekiston to'qimachilik sanoatida keng qo'llaniladi. Paxta eksporti sifat nazoratida muhim. ISO 6945:1990 asosida CIS uchun moslashtirilgan.",
        "Метод определения линейной плотности хлопкового волокна. Широко применяется в текстильной промышленности Узбекистана. Важен при экспортном контроле качества хлопка. Разработан на основе ISO 6945:1990 для стран СНГ.",
        "Method for determining linear density of cotton fibre. Widely applied in Uzbekistan's textile industry. Important for export quality control of cotton. Developed based on ISO 6945:1990 for CIS countries.",
    ),
    (
        "GOST R 56020-2014",
        "Tejamkor ishlab chiqarish — Asosiy qoidalar va lug'at",
        "Бережливое производство — Основные положения и словарь",
        "Lean production — Basic provisions and vocabulary",
        "2014", "Mashinasozlik",
        "Lean Production (Tejamkor ishlab chiqarish) — asosiy qoidalar va terminologiya. Toyota ishlab chiqarish tizimi (TPS) tamoyillariga asoslangan. Rossiya sanoatida keng joriy etilmoqda; O'zbekiston korxonalarida qo'llanila boshlandi.",
        "Основные положения и терминология бережливого производства (Lean Production). Основан на принципах производственной системы Toyota (TPS). Широко внедряется в промышленности России и начинает применяться в Узбекистане.",
        "Basic provisions and terminology for lean production. Based on Toyota Production System (TPS) principles. Widely adopted in Russian industry; gaining traction in Uzbekistan.",
    ),
    (
        "GOST 2.105-2019",
        "Konstruktorlik hujjatlari yagona tizimi — Matnli hujjatlarga umumiy talablar",
        "Единая система конструкторской документации — Общие требования к текстовым документам",
        "Unified system for design documentation — General requirements for text documents",
        "2019", "Mashinasozlik",
        "Konstruktorlik hujjatlari yagona tizimi — matnli hujjatlarga umumiy talablar. O'zbekiston mashinasozlik va muhandislik sohasida keng qo'llaniladi. Loyihalar va texnik hujjatlar uchun majburiy format.",
        "Общие требования к текстовым конструкторским документам в ЕСКД. Широко применяется в машиностроении и инженерии Узбекистана. Обязательный формат для проектной и технической документации.",
        "General requirements for textual design documents in the unified system. Widely applied in Uzbekistan's machinery manufacturing and engineering. Mandatory format for project and technical documentation.",
    ),
    (
        "GOST R ISO 22000-2019",
        "Oziq-ovqat mahsulotlari xavfsizligi menejmenti tizimlari — Oziq-ovqat zanjirida ishtirok etuvchi tashkilotlarga talablar",
        "Системы менеджмента безопасности пищевой продукции — Требования к организациям, участвующим в цепи создания пищевой продукции",
        "Food safety management systems — Requirements for organizations in the food chain",
        "2019", "Oziq-ovqat",
        "ISO 22000:2018 ning Rossiya milliy versiyasi (GOST R). O'zbekistonda Rossiyaga oziq-ovqat eksport qiluvchi korxonalar uchun muhim. HACCP tamoyillari bilan birga qo'llaniladi.",
        "Российская национальная версия ISO 22000:2018 (ГОСТ Р). Для предприятий Узбекистана, экспортирующих пищевую продукцию в Россию. Включает принципы ХАССП.",
        "Russian national version (GOST R) of ISO 22000:2018. Relevant for Uzbekistan enterprises exporting food products to Russia. Incorporates HACCP principles.",
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

            for row in standards:
                code, name_uz, name_ru, name_en, version, industry_name, desc_uz, desc_ru, desc_en = row
                industry = get_or_create_industry(industry_name)
                obj, was_created = Standard.objects.get_or_create(
                    code=code,
                    defaults={
                        'name': name_uz,
                        'name_ru': name_ru,
                        'name_en': name_en,
                        'type': std_type,
                        'version': version,
                        'industry': industry,
                        'description': desc_uz,
                        'description_ru': desc_ru,
                        'description_en': desc_en,
                        'is_active': True,
                    },
                )
                if was_created:
                    created += 1
                    self.stdout.write(f'  ✓ {code}')
                else:
                    changed = False
                    for field, val in [
                        ('name', name_uz), ('name_ru', name_ru), ('name_en', name_en),
                        ('description', desc_uz), ('description_ru', desc_ru), ('description_en', desc_en),
                        ('version', version),
                    ]:
                        if getattr(obj, field) != val:
                            setattr(obj, field, val)
                            changed = True
                    if obj.industry_id != industry.pk:
                        obj.industry = industry
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
