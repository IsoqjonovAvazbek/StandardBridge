"""
Management command: seed_questions

Gap-analiz savollari yuklaydi. Har standart uchun o'z savollari.
UzDST/GOST standartlari ISO ekvivalenti bilan bir xil savollardan foydalanadi
(chunki ular bir xil standartning milliy versiyasi).

    python manage.py seed_questions
    python manage.py seed_questions --reset  # Qayta yaratish
"""
from django.core.management.base import BaseCommand
from analysis.models import Standard, Question


# ─── ISO 9001 savollari (sifat menejmenti) ────────────────────────────────────
Q_9001 = [
    ('Sizda sifat siyosati hujjatlashtirilganmi?',                   '5.2 Quality policy'),
    ('Rahbariyat sifat tizimiga mas\'ulmi?',                          '5.1 Leadership'),
    ('Tashkilot konteksti va manfaatdor tomonlar aniqlanganmi?',      '4.1/4.2 Context'),
    ('QMS doirasi (scope) hujjatlashtirilganmi?',                    '4.3 Scope'),
    ('Xodimlar malakasi baholanadi va hujjatlashtiriladimi?',        '7.2 Competence'),
    ('Hujjatlar nazorati tizimi bormi?',                             '7.5 Documented info'),
    ('Ichki auditlar muntazam o\'tkaziladimi?',                       '9.2 Internal audit'),
    ('Rahbariyat tahlili (management review) o\'tkaziladimi?',        '9.3 Management review'),
    ('Nomuvofiqliklar qayd etiladi va tuzatiladimi?',                '10.2 Nonconformity'),
    ('Mijoz qoniqishi o\'lchanadi va tahlil qilinadimi?',             '9.1.2 Customer satisfaction'),
    ('Korrektiv choralar qo\'llaniladimi?',                           '10.2 Corrective actions'),
    ('Risk va imkoniyatlar baholanadimi?',                           '6.1 Risks & opportunities'),
    ('Jarayonlar aniqlangan va o\'zaro bog\'liqligi belgilanganmi?',  '4.4 Process approach'),
    ('Sifat maqsadlari o\'lchanadigan va kuzatiladimi?',              '6.2 Quality objectives'),
    ('Yetkazib beruvchilar baholanadi va nazorat qilinadimi?',       '8.4 External providers'),
]

# ─── ISO 22000 savollari (oziq-ovqat xavfsizligi) ────────────────────────────
Q_22000 = [
    ('Oziq-ovqat xavfsizligi siyosati hujjatlashtirilganmi?',        '5.2 Food safety policy'),
    ('HACCP rejasi ishlab chiqilganmi?',                             '8.5 HACCP plan'),
    ('Muhim nazorat nuqtalari (CCP) aniqlanganmi?',                  '8.5.4 CCPs'),
    ('Old shart dasturlari (PRP) joriy etilganmi?',                  '8.2 PRPs'),
    ('Xavf tahlili (hazard analysis) o\'tkazilganmi?',               '8.4 Hazard analysis'),
    ('Mahsulot kuzatuvchanligi (traceability) tizimi bormi?',        '8.9.5 Traceability'),
    ('Qaytarib olish (recall) protsedurasi mavjudmi?',               '8.9.5 Recall/withdrawal'),
    ('Gigiyena va sanitariya talablari bajariladimi?',               '8.2.4 Hygiene'),
    ('Allergenlar nazorat qilinadimi?',                              '8.2.4 Allergen control'),
    ('Xodimlarning oziq-ovqat xavfsizligi bo\'yicha trening bormi?', '7.2 Competence'),
    ('Monitoring va o\'lchov natijalari qayd etiladimi?',            '8.8 Verification'),
    ('Ichki va tashqi aloqa (communication) tizimi bormi?',          '7.4 Communication'),
]

# ─── ISO 14001 savollari (atrof-muhit) ───────────────────────────────────────
Q_14001 = [
    ('Atrof-muhit siyosati hujjatlashtirilganmi?',                   '5.2 Environmental policy'),
    ('Ekologik aspektlar (environmental aspects) aniqlanganmi?',     '6.1.2 Env. aspects'),
    ('Qonuniy va boshqa ekologik talablar ro\'yxati yuritiladimi?',  '6.1.3 Legal requirements'),
    ('Ekologik maqsadlar va dasturlar belgilanganmi?',               '6.2 Objectives'),
    ('Chiqindilar boshqaruvi tizimi bormi?',                         '8.1 Waste management'),
    ('Energiya va resurs iste\'moli nazorat qilinadimi?',            '8.1 Resource use'),
    ('Favqulodda ekologik vaziyatlarga tayyorgarlik rejasi bormi?',  '8.2 Emergency prep.'),
    ('Ekologik ko\'rsatkichlar monitoring qilinadimi?',               '9.1 Monitoring'),
    ('Xodimlar ekologik mas\'uliyat bo\'yicha o\'qitiladimi?',        '7.2 Competence'),
    ('Ichki ekologik auditlar o\'tkaziladimi?',                       '9.2 Internal audit'),
    ('Ifloslanishning oldini olish choralari bormi?',                '8.1 Pollution prevention'),
    ('Rahbariyat tahlili o\'tkaziladimi?',                           '9.3 Management review'),
]

# ─── ISO 45001 savollari (mehnat xavfsizligi) ────────────────────────────────
Q_45001 = [
    ('Mehnat xavfsizligi siyosati hujjatlashtirilganmi?',            '5.2 OH&S policy'),
    ('Xavf-xatarlar aniqlanadi va baholanadimi?',                    '6.1.2 Hazard identification'),
    ('Risklarni baholash (risk assessment) o\'tkaziladimi?',          '6.1.2 Risk assessment'),
    ('Xodimlar maslahatlashuvi va ishtiroki ta\'minlanadimi?',        '5.4 Worker participation'),
    ('Shaxsiy himoya vositalari (PPE) ta\'minlanadimi?',              '8.1.2 PPE'),
    ('Baxtsiz hodisalar qayd etiladi va tekshiriladimi?',            '10.2 Incident investigation'),
    ('Favqulodda xavfsizlik vaziyatlari rejasi mavjudmi?',           '8.2 Emergency preparedness'),
    ('Xavfsizlik bo\'yicha treninglar o\'tkaziladimi?',               '7.2 Competence'),
    ('Sog\'liq monitoringi (health surveillance) bormi?',             '8.6.1 Health surveillance'),
    ('Qonuniy mehnat muhofazasi talablari bajariladimi?',            '6.1.3 Legal compliance'),
    ('Ichki MMX auditlari o\'tkaziladimi?',                           '9.2 Internal audit'),
    ('Rahbariyat tahlili o\'tkaziladimi?',                           '9.3 Management review'),
]

# ─── ISO/IEC 27001 savollari (axborot xavfsizligi) ───────────────────────────
Q_27001 = [
    ('Axborot xavfsizligi siyosati hujjatlashtirilganmi?',           '5.2 IS policy'),
    ('Axborot xavfsizligi risklari baholanganmi?',                   '6.1.2 Risk assessment'),
    ('Risklar bilan ishlash rejasi (risk treatment) bormi?',         '6.1.3 Risk treatment'),
    ('Kirish huquqlari (access control) nazorat qilinadimi?',        'A.9 Access control'),
    ('Kriptografiya va ma\'lumotlarni himoyalash amaliyoti bormi?',   'A.10 Cryptography'),
    ('Xavfsizlik hodisalari (incidents) qayd etiladi va tekshiriladimi?', 'A.16 Incident mgmt'),
    ('Xodimlar axborot xavfsizligi bo\'yicha o\'qitiladimi?',         '7.2/A.7 Awareness'),
    ('Tizimlar va tarmoqlar monitoringi bormi?',                     'A.12 Operations security'),
    ('Biznes uzluksizligi (business continuity) rejasi bormi?',      'A.17 BC management'),
    ('Uchinchi tomon (vendor) xavfsizligi baholanadimi?',            'A.15 Supplier security'),
    ('Ichki ISMS auditi o\'tkaziladimi?',                             '9.2 Internal audit'),
    ('Rahbariyat tahlili o\'tkaziladimi?',                           '9.3 Management review'),
]

# ─── ISO 50001 savollari (energiya menejmenti) ───────────────────────────────
Q_50001 = [
    ('Energiya siyosati hujjatlashtirilganmi?',                      '5.2 Energy policy'),
    ('Asosiy energiya foydalanish sohalari (SEU) aniqlanganmi?',     '6.3 Energy review'),
    ('Energiya bazaviy ko\'rsatkichi (EnB) belgilanganmi?',           '6.5 Energy baseline'),
    ('Energiya samaradorligi maqsadlari (EnPI) o\'rnatilganmi?',     '6.6 Energy objectives'),
    ('Energiya xaridlari (procurement) nazorat qilinadimi?',        '8.3 Energy procurement'),
    ('Katta energiya sarflovchi uskunalar monitoring qilinadimi?',   '9.1 Monitoring'),
    ('Energiya tejash loyihalari amalga oshirilyaptimi?',            '8.1 Operational control'),
    ('Xodimlar energiya tejashga o\'qitiladimi?',                     '7.2/7.3 Competence'),
    ('Ichki energiya auditi o\'tkaziladimi?',                         '9.2 Internal audit'),
    ('Rahbariyat tahlili o\'tkaziladimi?',                           '9.3 Management review'),
    ('Qonuniy energiya tejamkorligi talablari bajariladimi?',        '6.1.3 Legal req.'),
    ('Yangi loyihalarda energiya samaradorligi hisobga olinadimi?',  '8.2 Design'),
]

# ─── ISO 13485 savollari (tibbiy qurilmalar) ─────────────────────────────────
Q_13485 = [
    ('Sifat menejmenti tizimi tibbiy qurilmalarga moslashtiriganmi?', '4.1 QMS scope'),
    ('Mahsulot xavfsizligi va ish samaradorligi talablari aniqlanganmi?', '7.1 Planning'),
    ('Dizayn va ishlab chiqish (design & development) nazorat qilinadimi?', '7.3 Design'),
    ('Steril qurilmalar uchun validatsiya o\'tkaziladimi?',           '7.5.6 Sterile validation'),
    ('Kuzatuvchanlik (traceability) — implantlar uchun to\'liq?',    '7.5.9 Traceability'),
    ('Mijoz (bozor) talablari to\'g\'ri aniqlanganmi?',               '7.2 Customer reqs'),
    ('Yetkazib beruvchilar sifati nazorat qilinadimi?',              '7.4 Purchasing'),
    ('Baxtsiz hodisalar va qaytarib olish (recall) tizimi bormi?',   '8.2.3 Feedback'),
    ('Xodimlar malakasi tasdiqlangan va hujjatlashtirilganmi?',      '6.2 Competence'),
    ('Ichki auditlar o\'tkaziladimi?',                                '8.2.4 Internal audit'),
    ('Nomuvofiq mahsulotlar nazorat qilinadimi?',                    '8.3 Nonconforming product'),
    ('Rahbariyat tahlili o\'tkaziladimi?',                           '5.6 Management review'),
]

# ─── ISO 17025 savollari (laboratoriya) ──────────────────────────────────────
Q_17025 = [
    ('Laboratoriya beynalminal sifatida aniqlangan va mustaqilmi?',  '4.1 Impartiality'),
    ('Kompetentlik talablari (texnik xodimlar) hujjatlashtirilganmi?', '6.2 Personnel'),
    ('Jihozlar (uskunalar) kalibrlangan va tekshirilganmi?',         '6.4 Equipment'),
    ('Sinov va kalibrlash usullari validatsiya qilinganmi?',         '7.2 Method validation'),
    ('Namunalar uchun me\'yoriy sharoitlar ta\'minlanganmi?',         '7.4 Handling'),
    ('O\'lchov aniqlik darajasi (measurement uncertainty) hisoblanganmi?', '7.6 Measurement uncertainty'),
    ('Natijalar sifati nazorat qilinadimi (QC charts)?',             '7.7 Quality assurance'),
    ('Sinov natijalari hisobot formati standartlarga muvofiqmi?',    '7.8 Reporting'),
    ('Shikoyatlar qayd etiladi va ko\'rib chiqiladimi?',              '7.9 Complaints'),
    ('Ichki auditlar o\'tkaziladimi?',                                '8.7 Internal audits'),
    ('Tashqi laboratoriya tekshiruvlarida (PT) ishtirok etasizmi?',  '7.7 Proficiency testing'),
    ('Rahbariyat tahlili o\'tkaziladimi?',                           '8.9 Management review'),
]


# ─── Kalit → savol to'plami xaritasi ─────────────────────────────────────────
# Standart kodi ichida shu kalit bo'lsa, u savollar qo'llaniladi
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
                            help='Barcha savollarni o\'chirib qayta yaratish')

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
                continue  # Bu standart uchun savol to'plami yo'q

            created = 0
            for i, (text, clause) in enumerate(matched_questions):
                _, was_created = Question.objects.get_or_create(
                    standard=std,
                    text=text,
                    defaults={
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
