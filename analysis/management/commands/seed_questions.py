"""
Management command: seed_questions

Gap-analiz savollari yuklaydi. Har standart uchun o'z savollari.
UzDST/GOST standartlari ISO ekvivalenti bilan bir xil savollardan foydalanadi.

    python manage.py seed_questions
    python manage.py seed_questions --reset  # Qayta yaratish
"""
from django.core.management.base import BaseCommand
from analysis.models import Standard, Question


# Each entry: (uz_text, clause, ru_text, en_text)

# ─── ISO 9001 savollari ───────────────────────────────────────────────────────
Q_9001 = [
    ('Sizda sifat siyosati hujjatlashtirilganmi?',
     '5.2 Quality policy',
     'Задокументирована ли политика качества?',
     'Is the quality policy documented?'),
    ("Rahbariyat sifat tizimiga mas'ulmi?",
     '5.1 Leadership',
     'Несёт ли руководство ответственность за систему качества?',
     'Is management responsible for the quality system?'),
    ("Tashkilot konteksti va manfaatdor tomonlar aniqlanganmi?",
     '4.1/4.2 Context',
     'Определены ли контекст организации и заинтересованные стороны?',
     'Are the organizational context and interested parties identified?'),
    ('QMS doirasi (scope) hujjatlashtirilganmi?',
     '4.3 Scope',
     'Задокументирована ли область применения СМК?',
     'Is the QMS scope documented?'),
    ("Xodimlar malakasi baholanadi va hujjatlashtiriladimi?",
     '7.2 Competence',
     'Оценивается и документируется ли компетентность сотрудников?',
     'Is staff competence evaluated and documented?'),
    ("Hujjatlar nazorati tizimi bormi?",
     '7.5 Documented info',
     'Существует ли система управления документированной информацией?',
     'Is there a documented information control system?'),
    ("Ichki auditlar muntazam o'tkaziladimi?",
     '9.2 Internal audit',
     'Проводятся ли регулярные внутренние аудиты?',
     'Are internal audits conducted regularly?'),
    ("Rahbariyat tahlili (management review) o'tkaziladimi?",
     '9.3 Management review',
     'Проводится ли анализ со стороны руководства?',
     'Is a management review conducted?'),
    ("Nomuvofiqliklar qayd etiladi va tuzatiladimi?",
     '10.2 Nonconformity',
     'Регистрируются и устраняются ли несоответствия?',
     'Are nonconformities recorded and corrected?'),
    ("Mijoz qoniqishi o'lchanadi va tahlil qilinadimi?",
     '9.1.2 Customer satisfaction',
     'Измеряется и анализируется ли удовлетворённость клиентов?',
     'Is customer satisfaction measured and analyzed?'),
    ("Korrektiv choralar qo'llaniladimi?",
     '10.2 Corrective actions',
     'Принимаются ли корректирующие меры?',
     'Are corrective actions applied?'),
    ("Risk va imkoniyatlar baholanadimi?",
     '6.1 Risks & opportunities',
     'Оцениваются ли риски и возможности?',
     'Are risks and opportunities assessed?'),
    ("Jarayonlar aniqlangan va o'zaro bog'liqligi belgilanganmi?",
     '4.4 Process approach',
     'Определены ли процессы и их взаимосвязи?',
     'Are processes identified and their interactions defined?'),
    ("Sifat maqsadlari o'lchanadigan va kuzatiladimi?",
     '6.2 Quality objectives',
     'Являются ли цели в области качества измеримыми и отслеживаемыми?',
     'Are quality objectives measurable and monitored?'),
    ("Yetkazib beruvchilar baholanadi va nazorat qilinadimi?",
     '8.4 External providers',
     'Оцениваются и контролируются ли поставщики?',
     'Are suppliers evaluated and controlled?'),
]

# ─── ISO 22000 savollari ──────────────────────────────────────────────────────
Q_22000 = [
    ("Oziq-ovqat xavfsizligi siyosati hujjatlashtirilganmi?",
     '5.2 Food safety policy',
     'Задокументирована ли политика безопасности пищевых продуктов?',
     'Is the food safety policy documented?'),
    ("HACCP rejasi ishlab chiqilganmi?",
     '8.5 HACCP plan',
     'Разработан ли план HACCP?',
     'Is the HACCP plan developed?'),
    ("Muhim nazorat nuqtalari (CCP) aniqlanganmi?",
     '8.5.4 CCPs',
     'Определены ли критические контрольные точки (ККТ)?',
     'Are critical control points (CCPs) identified?'),
    ("Old shart dasturlari (PRP) joriy etilganmi?",
     '8.2 PRPs',
     'Внедрены ли программы обязательных предварительных условий (ПОУ)?',
     'Are prerequisite programmes (PRPs) implemented?'),
    ("Xavf tahlili (hazard analysis) o'tkazilganmi?",
     '8.4 Hazard analysis',
     'Проведён ли анализ опасных факторов?',
     'Has a hazard analysis been conducted?'),
    ("Mahsulot kuzatuvchanligi (traceability) tizimi bormi?",
     '8.9.5 Traceability',
     'Существует ли система прослеживаемости продукции?',
     'Is there a product traceability system?'),
    ("Qaytarib olish (recall) protsedurasi mavjudmi?",
     '8.9.5 Recall/withdrawal',
     'Существует ли процедура отзыва продукции?',
     'Is there a product recall procedure?'),
    ("Gigiyena va sanitariya talablari bajariladimi?",
     '8.2.4 Hygiene',
     'Соблюдаются ли требования гигиены и санитарии?',
     'Are hygiene and sanitation requirements met?'),
    ("Allergenlar nazorat qilinadimi?",
     '8.2.4 Allergen control',
     'Контролируются ли аллергены?',
     'Are allergens controlled?'),
    ("Xodimlarning oziq-ovqat xavfsizligi bo'yicha trening bormi?",
     '7.2 Competence',
     'Проводится ли обучение сотрудников по безопасности пищевых продуктов?',
     'Is staff trained on food safety?'),
    ("Monitoring va o'lchov natijalari qayd etiladimi?",
     '8.8 Verification',
     'Регистрируются ли результаты мониторинга и измерений?',
     'Are monitoring and measurement results recorded?'),
    ("Ichki va tashqi aloqa (communication) tizimi bormi?",
     '7.4 Communication',
     'Существует ли система внутренней и внешней коммуникации?',
     'Is there an internal and external communication system?'),
]

# ─── ISO 14001 savollari ──────────────────────────────────────────────────────
Q_14001 = [
    ("Atrof-muhit siyosati hujjatlashtirilganmi?",
     '5.2 Environmental policy',
     'Задокументирована ли экологическая политика?',
     'Is the environmental policy documented?'),
    ("Ekologik aspektlar (environmental aspects) aniqlanganmi?",
     '6.1.2 Env. aspects',
     'Определены ли экологические аспекты?',
     'Are environmental aspects identified?'),
    ("Qonuniy va boshqa ekologik talablar ro'yxati yuritiladimi?",
     '6.1.3 Legal requirements',
     'Ведётся ли реестр правовых и иных экологических требований?',
     'Is a register of legal and other environmental requirements maintained?'),
    ("Ekologik maqsadlar va dasturlar belgilanganmi?",
     '6.2 Objectives',
     'Установлены ли экологические цели и программы?',
     'Are environmental objectives and programmes set?'),
    ("Chiqindilar boshqaruvi tizimi bormi?",
     '8.1 Waste management',
     'Существует ли система управления отходами?',
     'Is there a waste management system?'),
    ("Energiya va resurs iste'moli nazorat qilinadimi?",
     '8.1 Resource use',
     'Контролируется ли потребление энергии и ресурсов?',
     'Is energy and resource consumption controlled?'),
    ("Favqulodda ekologik vaziyatlarga tayyorgarlik rejasi bormi?",
     '8.2 Emergency prep.',
     'Существует ли план готовности к экологическим чрезвычайным ситуациям?',
     'Is there an environmental emergency preparedness plan?'),
    ("Ekologik ko'rsatkichlar monitoring qilinadimi?",
     '9.1 Monitoring',
     'Проводится ли мониторинг экологических показателей?',
     'Are environmental performance indicators monitored?'),
    ("Xodimlar ekologik mas'uliyat bo'yicha o'qitiladimi?",
     '7.2 Competence',
     'Обучаются ли сотрудники экологической ответственности?',
     'Are employees trained on environmental responsibility?'),
    ("Ichki ekologik auditlar o'tkaziladimi?",
     '9.2 Internal audit',
     'Проводятся ли внутренние экологические аудиты?',
     'Are internal environmental audits conducted?'),
    ("Ifloslanishning oldini olish choralari bormi?",
     '8.1 Pollution prevention',
     'Существуют ли меры по предотвращению загрязнения?',
     'Are pollution prevention measures in place?'),
    ("Rahbariyat tahlili o'tkaziladimi?",
     '9.3 Management review',
     'Проводится ли анализ со стороны руководства?',
     'Is a management review conducted?'),
]

# ─── ISO 45001 savollari ──────────────────────────────────────────────────────
Q_45001 = [
    ("Mehnat xavfsizligi siyosati hujjatlashtirilganmi?",
     '5.2 OH&S policy',
     'Задокументирована ли политика охраны труда?',
     'Is the OH&S policy documented?'),
    ("Xavf-xatarlar aniqlanadi va baholanadimi?",
     '6.1.2 Hazard identification',
     'Идентифицируются и оцениваются ли опасности?',
     'Are hazards identified and assessed?'),
    ("Risklarni baholash (risk assessment) o'tkaziladimi?",
     '6.1.2 Risk assessment',
     'Проводится ли оценка рисков?',
     'Is risk assessment conducted?'),
    ("Xodimlar maslahatlashuvi va ishtiroki ta'minlanadimi?",
     '5.4 Worker participation',
     'Обеспечивается ли консультация и участие работников?',
     'Is worker consultation and participation ensured?'),
    ("Shaxsiy himoya vositalari (PPE) ta'minlanadimi?",
     '8.1.2 PPE',
     'Обеспечиваются ли средства индивидуальной защиты (СИЗ)?',
     'Are personal protective equipment (PPE) provided?'),
    ("Baxtsiz hodisalar qayd etiladi va tekshiriladimi?",
     '10.2 Incident investigation',
     'Регистрируются и расследуются ли несчастные случаи?',
     'Are incidents recorded and investigated?'),
    ("Favqulodda xavfsizlik vaziyatlari rejasi mavjudmi?",
     '8.2 Emergency preparedness',
     'Существует ли план готовности к чрезвычайным ситуациям?',
     'Is there an emergency preparedness plan?'),
    ("Xavfsizlik bo'yicha treninglar o'tkaziladimi?",
     '7.2 Competence',
     'Проводятся ли тренинги по безопасности?',
     'Are safety trainings conducted?'),
    ("Sog'liq monitoringi (health surveillance) bormi?",
     '8.6.1 Health surveillance',
     'Существует ли медицинское наблюдение за работниками?',
     'Is health surveillance in place?'),
    ("Qonuniy mehnat muhofazasi talablari bajariladimi?",
     '6.1.3 Legal compliance',
     'Соблюдаются ли законодательные требования охраны труда?',
     'Are legal occupational safety requirements met?'),
    ("Ichki MMX auditlari o'tkaziladimi?",
     '9.2 Internal audit',
     'Проводятся ли внутренние аудиты СУОТ?',
     'Are internal OH&S audits conducted?'),
    ("Rahbariyat tahlili o'tkaziladimi?",
     '9.3 Management review',
     'Проводится ли анализ со стороны руководства?',
     'Is a management review conducted?'),
]

# ─── ISO 27001 savollari ──────────────────────────────────────────────────────
Q_27001 = [
    ("Axborot xavfsizligi siyosati hujjatlashtirilganmi?",
     '5.2 IS policy',
     'Задокументирована ли политика информационной безопасности?',
     'Is the information security policy documented?'),
    ("Axborot xavfsizligi risklari baholanganmi?",
     '6.1.2 Risk assessment',
     'Оценены ли риски информационной безопасности?',
     'Are information security risks assessed?'),
    ("Risklar bilan ishlash rejasi (risk treatment) bormi?",
     '6.1.3 Risk treatment',
     'Существует ли план обработки рисков?',
     'Is there a risk treatment plan?'),
    ("Kirish huquqlari (access control) nazorat qilinadimi?",
     'A.9 Access control',
     'Контролируются ли права доступа?',
     'Is access control managed?'),
    ("Kriptografiya va ma'lumotlarni himoyalash amaliyoti bormi?",
     'A.10 Cryptography',
     'Используются ли криптография и защита данных?',
     'Are cryptography and data protection practices in place?'),
    ("Xavfsizlik hodisalari (incidents) qayd etiladi va tekshiriladimi?",
     'A.16 Incident mgmt',
     'Регистрируются и расследуются ли инциденты безопасности?',
     'Are security incidents recorded and investigated?'),
    ("Xodimlar axborot xavfsizligi bo'yicha o'qitiladimi?",
     '7.2/A.7 Awareness',
     'Обучаются ли сотрудники информационной безопасности?',
     'Are employees trained on information security?'),
    ("Tizimlar va tarmoqlar monitoringi bormi?",
     'A.12 Operations security',
     'Осуществляется ли мониторинг систем и сетей?',
     'Is systems and network monitoring in place?'),
    ("Biznes uzluksizligi (business continuity) rejasi bormi?",
     'A.17 BC management',
     'Существует ли план обеспечения непрерывности бизнеса?',
     'Is there a business continuity plan?'),
    ("Uchinchi tomon (vendor) xavfsizligi baholanadimi?",
     'A.15 Supplier security',
     'Оценивается ли безопасность сторонних поставщиков?',
     'Is third-party (vendor) security assessed?'),
    ("Ichki ISMS auditi o'tkaziladimi?",
     '9.2 Internal audit',
     'Проводится ли внутренний аудит СУИБ?',
     'Is an internal ISMS audit conducted?'),
    ("Rahbariyat tahlili o'tkaziladimi?",
     '9.3 Management review',
     'Проводится ли анализ со стороны руководства?',
     'Is a management review conducted?'),
]

# ─── ISO 50001 savollari ──────────────────────────────────────────────────────
Q_50001 = [
    ("Energiya siyosati hujjatlashtirilganmi?",
     '5.2 Energy policy',
     'Задокументирована ли энергетическая политика?',
     'Is the energy policy documented?'),
    ("Asosiy energiya foydalanish sohalari (SEU) aniqlanganmi?",
     '6.3 Energy review',
     'Определены ли значимые области использования энергии (ЗПЭ)?',
     'Are significant energy uses (SEUs) identified?'),
    ("Energiya bazaviy ko'rsatkichi (EnB) belgilanganmi?",
     '6.5 Energy baseline',
     'Установлена ли базовая линия потребления энергии (EnB)?',
     'Is an energy baseline (EnB) established?'),
    ("Energiya samaradorligi maqsadlari (EnPI) o'rnatilganmi?",
     '6.6 Energy objectives',
     'Установлены ли показатели энергетической эффективности (EnPI)?',
     'Are energy performance indicators (EnPI) set?'),
    ("Energiya xaridlari (procurement) nazorat qilinadimi?",
     '8.3 Energy procurement',
     'Контролируются ли закупки энергии?',
     'Is energy procurement controlled?'),
    ("Katta energiya sarflovchi uskunalar monitoring qilinadimi?",
     '9.1 Monitoring',
     'Ведётся ли мониторинг крупных энергопотребляющих объектов?',
     'Are major energy-consuming equipment monitored?'),
    ("Energiya tejash loyihalari amalga oshirilyaptimi?",
     '8.1 Operational control',
     'Реализуются ли проекты по энергосбережению?',
     'Are energy-saving projects being implemented?'),
    ("Xodimlar energiya tejashga o'qitiladimi?",
     '7.2/7.3 Competence',
     'Обучаются ли сотрудники энергосбережению?',
     'Are employees trained on energy saving?'),
    ("Ichki energiya auditi o'tkaziladimi?",
     '9.2 Internal audit',
     'Проводится ли внутренний энергетический аудит?',
     'Is an internal energy audit conducted?'),
    ("Rahbariyat tahlili o'tkaziladimi?",
     '9.3 Management review',
     'Проводится ли анализ со стороны руководства?',
     'Is a management review conducted?'),
    ("Qonuniy energiya tejamkorligi talablari bajariladimi?",
     '6.1.3 Legal req.',
     'Соблюдаются ли законодательные требования по энергоэффективности?',
     'Are legal energy efficiency requirements met?'),
    ("Yangi loyihalarda energiya samaradorligi hisobga olinadimi?",
     '8.2 Design',
     'Учитывается ли энергоэффективность при реализации новых проектов?',
     'Is energy efficiency considered in new project designs?'),
]

# ─── ISO 13485 savollari ──────────────────────────────────────────────────────
Q_13485 = [
    ("Sifat menejmenti tizimi tibbiy qurilmalarga moslashtiriganmi?",
     '4.1 QMS scope',
     'Адаптирована ли СМК для медицинских изделий?',
     'Is the QMS adapted for medical devices?'),
    ("Mahsulot xavfsizligi va ish samaradorligi talablari aniqlanganmi?",
     '7.1 Planning',
     'Определены ли требования к безопасности и эффективности продукта?',
     'Are product safety and performance requirements identified?'),
    ("Dizayn va ishlab chiqish (design & development) nazorat qilinadimi?",
     '7.3 Design',
     'Контролируются ли проектирование и разработка?',
     'Is design and development controlled?'),
    ("Steril qurilmalar uchun validatsiya o'tkaziladimi?",
     '7.5.6 Sterile validation',
     'Проводится ли валидация для стерильных изделий?',
     'Is validation conducted for sterile devices?'),
    ("Kuzatuvchanlik (traceability) — implantlar uchun to'liq?",
     '7.5.9 Traceability',
     'Обеспечена ли полная прослеживаемость для имплантатов?',
     'Is traceability complete for implants?'),
    ("Mijoz (bozor) talablari to'g'ri aniqlanganmi?",
     '7.2 Customer reqs',
     'Правильно ли определены требования клиентов (рынка)?',
     'Are customer (market) requirements correctly identified?'),
    ("Yetkazib beruvchilar sifati nazorat qilinadimi?",
     '7.4 Purchasing',
     'Контролируется ли качество поставщиков?',
     'Is supplier quality controlled?'),
    ("Baxtsiz hodisalar va qaytarib olish (recall) tizimi bormi?",
     '8.2.3 Feedback',
     'Существует ли система учёта инцидентов и отзыва продукции?',
     'Is there an incident and recall system?'),
    ("Xodimlar malakasi tasdiqlangan va hujjatlashtirilganmi?",
     '6.2 Competence',
     'Подтверждена и задокументирована ли компетентность сотрудников?',
     'Is staff competence confirmed and documented?'),
    ("Ichki auditlar o'tkaziladimi?",
     '8.2.4 Internal audit',
     'Проводятся ли внутренние аудиты?',
     'Are internal audits conducted?'),
    ("Nomuvofiq mahsulotlar nazorat qilinadimi?",
     '8.3 Nonconforming product',
     'Контролируется ли несоответствующая продукция?',
     'Are nonconforming products controlled?'),
    ("Rahbariyat tahlili o'tkaziladimi?",
     '5.6 Management review',
     'Проводится ли анализ со стороны руководства?',
     'Is a management review conducted?'),
]

# ─── ISO 17025 savollari ──────────────────────────────────────────────────────
Q_17025 = [
    ("Laboratoriya beynalminal sifatida aniqlangan va mustaqilmi?",
     '4.1 Impartiality',
     'Определена ли независимость и беспристрастность лаборатории?',
     'Is the laboratory defined as impartial and independent?'),
    ("Kompetentlik talablari (texnik xodimlar) hujjatlashtirilganmi?",
     '6.2 Personnel',
     'Задокументированы ли требования к компетентности технического персонала?',
     'Are competence requirements for technical personnel documented?'),
    ("Jihozlar (uskunalar) kalibrlangan va tekshirilganmi?",
     '6.4 Equipment',
     'Откалибровано и проверено ли оборудование?',
     'Is equipment calibrated and verified?'),
    ("Sinov va kalibrlash usullari validatsiya qilinganmi?",
     '7.2 Method validation',
     'Валидированы ли методы испытаний и калибровки?',
     'Are test and calibration methods validated?'),
    ("Namunalar uchun me'yoriy sharoitlar ta'minlanganmi?",
     '7.4 Handling',
     'Обеспечены ли нормативные условия хранения образцов?',
     'Are standard conditions for samples ensured?'),
    ("O'lchov aniqlik darajasi (measurement uncertainty) hisoblanganmi?",
     '7.6 Measurement uncertainty',
     'Рассчитана ли неопределённость измерений?',
     'Is measurement uncertainty calculated?'),
    ("Natijalar sifati nazorat qilinadimi (QC charts)?",
     '7.7 Quality assurance',
     'Контролируется ли качество результатов (QC-диаграммы)?',
     'Is result quality monitored (QC charts)?'),
    ("Sinov natijalari hisobot formati standartlarga muvofiqmi?",
     '7.8 Reporting',
     'Соответствует ли формат отчётов по испытаниям стандартам?',
     'Does the test report format meet standards?'),
    ("Shikoyatlar qayd etiladi va ko'rib chiqiladimi?",
     '7.9 Complaints',
     'Регистрируются и рассматриваются ли жалобы?',
     'Are complaints recorded and reviewed?'),
    ("Ichki auditlar o'tkaziladimi?",
     '8.7 Internal audits',
     'Проводятся ли внутренние аудиты?',
     'Are internal audits conducted?'),
    ("Tashqi laboratoriya tekshiruvlarida (PT) ishtirok etasizmi?",
     '7.7 Proficiency testing',
     'Участвуете ли вы во внешних проверках лаборатории (МСИ)?',
     'Do you participate in external proficiency testing (PT)?'),
    ("Rahbariyat tahlili o'tkaziladimi?",
     '8.9 Management review',
     'Проводится ли анализ со стороны руководства?',
     'Is a management review conducted?'),
]


# ─── Kalit → savol to'plami xaritasi ─────────────────────────────────────────
QUESTIONS_MAP = {
    '9001':  Q_9001,
    '22000': Q_22000,
    '14001': Q_14001,
    '45001': Q_45001,
    '27001': Q_27001,
    '50001': Q_50001,
    '13485': Q_13485,
    '17025': Q_17025,
}


class Command(BaseCommand):
    help = 'Barcha standartlar uchun gap-analiz savollari yuklaydi (ISO, UzDST, GOST)'

    def add_arguments(self, parser):
        parser.add_argument('--reset', action='store_true',
                            help="Barcha savollarni o'chirib qayta yaratish")

    def handle(self, *args, **options):
        if options['reset']:
            deleted = Question.objects.all().delete()
            self.stdout.write(self.style.WARNING(f'  {deleted[0]} ta savol o\'chirildi.'))

        total_created = 0
        total_skipped = 0

        all_standards = Standard.objects.filter(is_active=True).order_by('code')

        for std in all_standards:
            matched_questions = None
            for key, q_list in QUESTIONS_MAP.items():
                if key in std.code:
                    matched_questions = q_list
                    break

            if matched_questions is None:
                continue

            created = 0
            for i, (text, clause, text_ru, text_en) in enumerate(matched_questions):
                obj, was_created = Question.objects.get_or_create(
                    standard=std,
                    text=text,
                    defaults={
                        'text_ru': text_ru,
                        'text_en': text_en,
                        'help_text': clause,
                        'order': i + 1,
                        'answer_type': 'yes_partial_no',
                        'is_active': True,
                    },
                )
                if was_created:
                    created += 1
                    total_created += 1
                else:
                    updated = False
                    if not obj.text_ru:
                        obj.text_ru = text_ru
                        updated = True
                    if not obj.text_en:
                        obj.text_en = text_en
                        updated = True
                    if updated:
                        obj.save(update_fields=['text_ru', 'text_en'])
                    total_skipped += 1

            if created > 0:
                self.stdout.write(f'  ✓ {std.code}: {created} ta yangi savol')
            else:
                self.stdout.write(f'  · {std.code}: allaqachon mavjud ({len(matched_questions)} ta)')

        self.stdout.write(self.style.SUCCESS(
            f'\n✅ {total_created} ta yangi savol qo\'shildi, {total_skipped} ta mavjud edi.'
        ))
        self.stdout.write(
            f'   Qamrab olilgan standartlar: ISO 9001/14001/45001/22000/27001/50001/13485/17025\n'
            f'   va ularning barcha UzDST/GOST ekvivalentlari'
        )
