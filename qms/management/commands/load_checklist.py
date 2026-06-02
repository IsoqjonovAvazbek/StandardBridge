"""
Management command: load_checklist

Populates ChecklistItem table with standard-specific questions.
Run once after migrations:
    python manage.py load_checklist

Re-running is safe — it deletes and recreates items per standard.
"""

from django.core.management.base import BaseCommand
from qms.models import ChecklistItem


# ── ISO 9001:2015 — Quality Management System ─────────────────────────────
ISO9001_ITEMS = [
    # Clause 4 — Context
    ("Tashkilot konteksti va manfaatdor tomonlar aniqlanganmi?", "ISO 9001:2015 — 4.1 / 4.2"),
    ("QMS doirasi (scope) hujjatlashtirilganmi?", "ISO 9001:2015 — 4.3"),
    ("QMS jarayonlari va ularning o'zaro bog'liqligi aniqlanganmi?", "ISO 9001:2015 — 4.4"),
    # Clause 5 — Leadership
    ("Rahbariyat QMSga o'z majburiyatini namoyon etadimi?", "ISO 9001:2015 — 5.1"),
    ("Sifat siyosati mavjud, tarqatilgan va tushunilganmi?", "ISO 9001:2015 — 5.2"),
    ("Mas'uliyat va vakolatlar aniq belgilanib, tarqatilganmi?", "ISO 9001:2015 — 5.3"),
    # Clause 6 — Planning
    ("Risklarni va imkoniyatlarni boshqarish jarayoni bormi?", "ISO 9001:2015 — 6.1"),
    ("Sifat maqsadlari o'lchanadigan va kuzatiladimi?", "ISO 9001:2015 — 6.2"),
    ("O'zgarishlarni rejalashtirish jarayoni mavjudmi?", "ISO 9001:2015 — 6.3"),
    # Clause 7 — Support
    ("Kerakli resurslar (odam, infratuzilma, muhit) ta'minlanganmi?", "ISO 9001:2015 — 7.1"),
    ("Xodimlar vakolati va malakasi ta'minlanganmi?", "ISO 9001:2015 — 7.2"),
    ("Xodimlar sifat siyosati haqida xabardormi?", "ISO 9001:2015 — 7.3"),
    ("Ichki va tashqi kommunikatsiya jarayoni aniq belgilanganmi?", "ISO 9001:2015 — 7.4"),
    ("Hujjatlashtirilgan ma'lumotlar boshqaruvi (yaratish, yangilash, nazorat) mavjudmi?", "ISO 9001:2015 — 7.5"),
    # Clause 8 — Operation
    ("Mahsulot / xizmat talablari aniqlanib, tekshirilganmi?", "ISO 9001:2015 — 8.2"),
    ("Dizayn va ishlab chiqish jarayoni nazorat qilinadimi?", "ISO 9001:2015 — 8.3"),
    ("Tashqi ta'minotchilar va ularning natijalari nazorat qilinadimi?", "ISO 9001:2015 — 8.4"),
    ("Mahsulot / xizmat ko'rsatish jarayoni boshqariladimi?", "ISO 9001:2015 — 8.5"),
    ("Chiqarish (release) nazorati va tegishli hujjatlar mavjudmi?", "ISO 9001:2015 — 8.6"),
    ("Nomuvofiq chiqarish boshqaruvi jarayoni mavjudmi?", "ISO 9001:2015 — 8.7"),
    # Clause 9 — Performance evaluation
    ("Mijoz qoniqishi o'lchanadi va tahlil qilinadimi?", "ISO 9001:2015 — 9.1.2"),
    ("Ichki auditlar rejalashtirilgan va o'tkaziladimi?", "ISO 9001:2015 — 9.2"),
    ("Menejment sharhi (management review) o'tkaziladimi?", "ISO 9001:2015 — 9.3"),
    # Clause 10 — Improvement
    ("Nomuvofiqliklar va tuzatuvchi choralar kuzatiladimi?", "ISO 9001:2015 — 10.2"),
    ("Doimiy yaxshilash jarayoni mavjud va faol ishlatilmoqdami?", "ISO 9001:2015 — 10.3"),
]

# ── ISO 22000:2018 — Food Safety Management ───────────────────────────────
ISO22000_ITEMS = [
    ("Oziq-ovqat xavfsizligi siyosati mavjud va tarqatilganmi?", "ISO 22000:2018 — 5.2"),
    ("HACCP guruhi tashkil etilganmi?", "ISO 22000:2018 — 7.1.2"),
    ("Mahsulot tavsifi va mo'ljallangan foydalanish hujjatlashtirilganmi?", "ISO 22000:2018 — 8.5.1"),
    ("Ishlab chiqarish jarayoni oqim diagrammasi tuzilganmi?", "ISO 22000:2018 — 8.5.1.4"),
    ("Xavflar tahlili (Hazard Analysis) o'tkazilganmi?", "ISO 22000:2018 — 8.5.2"),
    ("Nazorat choralari (Control Measures) belgilanganmi?", "ISO 22000:2018 — 8.5.4"),
    ("Kritik boshqaruv nuqtalari (CCP) aniqlanganmi?", "ISO 22000:2018 — 8.5.4"),
    ("Monitoring tizimi CCP lar uchun o'rnatilganmi?", "ISO 22000:2018 — 8.8"),
    ("Tuzatuvchi choralar jarayoni mavjudmi?", "ISO 22000:2018 — 8.9.3"),
    ("Tasdiqlash (Verification) faoliyatlari rejalashtirilganmi?", "ISO 22000:2018 — 8.8"),
    ("PRPs (Oldindan zarur dasturlar) o'rnatilganmi?", "ISO 22000:2018 — 8.2"),
    ("Ta'minot zanjiri boshqaruvi mavjudmi?", "ISO 22000:2018 — 8.4.1"),
    ("Xodimlar oziq-ovqat xavfsizligi bo'yicha o'qitilganmi?", "ISO 22000:2018 — 7.2"),
    ("Favqulodda holat va krizis boshqaruvi jarayoni bormi?", "ISO 22000:2018 — 8.4.2"),
    ("Ichki auditlar o'tkaziladimi?", "ISO 22000:2018 — 9.2"),
]

# ── ISO 14001:2015 — Environmental Management ─────────────────────────────
ISO14001_ITEMS = [
    ("Tashkilotning atrof-muhitga ta'sir qiladigan faoliyatlari aniqlanganmi?", "ISO 14001:2015 — 6.1.2"),
    ("Atrof-muhit siyosati mavjud va tarqatilganmi?", "ISO 14001:2015 — 5.2"),
    ("Atrof-muhit maqsadlari belgilanganmi?", "ISO 14001:2015 — 6.2"),
    ("Muhim atrof-muhit jihatlari (significant aspects) aniqlanganmi?", "ISO 14001:2015 — 6.1.2"),
    ("Qonuniy va boshqa talablar ro'yxati mavjudmi?", "ISO 14001:2015 — 6.1.3"),
    ("Atrof-muhit risklar va imkoniyatlari baholangan?", "ISO 14001:2015 — 6.1.1"),
    ("Favqulodda holat va baxtsiz hodisalarga tayyor jarayon bormi?", "ISO 14001:2015 — 8.2"),
    ("Chiqindilarni boshqarish jarayoni mavjudmi?", "ISO 14001:2015 — 8.1"),
    ("Energiya va resurslardan samarali foydalanish monitoringi?", "ISO 14001:2015 — 9.1"),
    ("Ichki auditlar o'tkaziladimi?", "ISO 14001:2015 — 9.2"),
    ("Menejment sharhi atrof-muhitni qamrab oladimi?", "ISO 14001:2015 — 9.3"),
    ("Nomuvofiqliklar va tuzatuvchi choralar mavjudmi?", "ISO 14001:2015 — 10.2"),
]

# ── ISO 45001:2018 — Occupational Health & Safety ─────────────────────────
ISO45001_ITEMS = [
    ("Mehnat xavfsizligi siyosati mavjud va tarqatilganmi?", "ISO 45001:2018 — 5.2"),
    ("Xavflarni aniqlash va risklarni baholash jarayoni bormi?", "ISO 45001:2018 — 6.1.2"),
    ("Xavfsizlik va sog'liqni saqlash maqsadlari belgilanganmi?", "ISO 45001:2018 — 6.2"),
    ("Ishchilarni ishtiroki va maslahati mexanizmi mavjudmi?", "ISO 45001:2018 — 5.4"),
    ("Qonuniy va boshqa OHS talablari aniqlanganmi?", "ISO 45001:2018 — 6.1.3"),
    ("Inshoot, jihozlar va jarayonlar xavfsizligi nazorat qilinadimi?", "ISO 45001:2018 — 8.1"),
    ("Favqulodda holat va baxtsiz hodisalarga tayyor jarayon bormi?", "ISO 45001:2018 — 8.2"),
    ("Baxtsiz hodisalar va yaqin miss-lar (near misses) hisobga olinadimi?", "ISO 45001:2018 — 9.1.1"),
    ("Xodimlar xavfsizlik bo'yicha o'qitilgan va sertifikatlashtirilganmi?", "ISO 45001:2018 — 7.2"),
    ("Shaxsiy himoya vositalari (PPE) ta'minlanganmi?", "ISO 45001:2018 — 8.1.2"),
    ("Ichki OHS auditlari o'tkaziladimi?", "ISO 45001:2018 — 9.2"),
    ("Nomuvofiqliklar va tuzatuvchi choralar kuzatiladimi?", "ISO 45001:2018 — 10.2"),
]

STANDARDS_DATA = [
    ('iso9001', ISO9001_ITEMS),
    ('iso22000', ISO22000_ITEMS),
    ('iso14001', ISO14001_ITEMS),
    ('iso45001', ISO45001_ITEMS),
]


class Command(BaseCommand):
    help = 'Load / reload ISO checklist items for all supported standards'

    def add_arguments(self, parser):
        parser.add_argument(
            '--standard',
            type=str,
            default='all',
            help='Load a specific standard only: iso9001 | iso22000 | iso14001 | iso45001 | all',
        )

    def handle(self, *args, **options):
        target = options['standard']
        total_created = 0

        for standard_code, items in STANDARDS_DATA:
            if target != 'all' and target != standard_code:
                continue

            created_count = 0
            for i, (question, requirement) in enumerate(items, start=1):
                _, created = ChecklistItem.objects.get_or_create(
                    standard=standard_code,
                    question=question,
                    defaults={
                        'requirement': requirement,
                        'order': i,
                    },
                )
                if created:
                    created_count += 1
            self.stdout.write(
                self.style.SUCCESS(
                    f"  {standard_code.upper()}: {created_count} ta yangi savol qo'shildi "
                    f"({len(items) - created_count} ta allaqachon bor)"
                )
            )
            total_created += created_count

        self.stdout.write(
            self.style.SUCCESS(f"\nJami {total_created} ta checklist item yaratildi.")
        )
