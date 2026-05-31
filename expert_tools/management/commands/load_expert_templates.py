"""
Management command: load_expert_templates

Populates DocumentTemplate and ProjectTemplate tables with starter data.
Safe to re-run — deletes existing records first.

    python manage.py load_expert_templates
"""

from django.core.management.base import BaseCommand
from expert_tools.models import DocumentTemplate, ProjectTemplate, ProjectTemplateStep


DOCUMENT_TEMPLATES = [
    {
        'title': 'Sifat siyosati',
        'doc_type': 'quality_policy',
        'standard': 'iso9001',
        'ai_prompt': (
            "ISO 9001:2015 talablariga mos professional sifat siyosati hujjatini O'zbek tilida yoz. "
            "Quyidagi bo'limlarni o'z ichiga olsin:\n"
            "1. Maqsad va doira\n2. Rahbariyat majburiyati\n"
            "3. Sifat maqsadlari\n4. Doimiy yaxshilash\n5. Xodimlar ishtiroki\n"
            "Hajmi: 1-2 sahifa. Rasmiy uslub."
        ),
    },
    {
        'title': 'Hujjatlarni boshqarish protsedurasI',
        'doc_type': 'procedure',
        'standard': 'iso9001',
        'ai_prompt': (
            "ISO 9001:2015 7.5-bandiga mos hujjatlarni boshqarish protsedurasi yoz. "
            "Maqsad, doira, mas'uliyat, protsedura qadamlari (yaratish→tasdiqlash→tarqatish→arxiv), "
            "va hujjatlar ro'yxatini o'z ichiga olsin."
        ),
    },
    {
        'title': 'Ichki audit protsedurasI',
        'doc_type': 'procedure',
        'standard': 'iso9001',
        'ai_prompt': (
            "ISO 9001:2015 9.2-bandiga mos ichki audit protsedurasi yoz. "
            "Audit rejalashtirish, auditorlar tanlash, o'tkazish, hisobot yozish "
            "va nomuvofiqliklarni kuzatish qadamlarini o'z ichiga olsin."
        ),
    },
    {
        'title': 'Tuzatuvchi chora protsedurasi',
        'doc_type': 'corrective_action',
        'standard': 'iso9001',
        'ai_prompt': (
            "ISO 9001:2015 10.2-bandiga mos nomuvofiqlik va tuzatuvchi choralar protsedurasi yoz. "
            "Muammoni aniqlash, ildiz sababini tahlil qilish (5-nima, baliq skeleti), "
            "chora belgilash, amalga oshirish va samaradorligini tekshirish qadamlari bo'lsin."
        ),
    },
    {
        'title': 'Menejment sharhi protsedurasI',
        'doc_type': 'management_review',
        'standard': 'iso9001',
        'ai_prompt': (
            "ISO 9001:2015 9.3-bandiga mos menejment sharhi protsedurasi yoz. "
            "Kirish ma'lumotlari (audit natijalari, mijoz fikri, maqsadlar holati), "
            "chiqish qarorlari, chastota (yiliga kamida 1 marta) va qatnashuvchilarni ko'rsatsin."
        ),
    },
    {
        'title': 'Xodimlar malakasini boshqarish protsedurasI',
        'doc_type': 'procedure',
        'standard': 'iso9001',
        'ai_prompt': (
            "ISO 9001:2015 7.2-bandiga mos xodimlar malakasini boshqarish protsedurasi yoz. "
            "Malaka talablari aniqlash, trening rejalashtirish, samaradorligini baholash "
            "va yozuvlarni saqlash bo'limlarini o'z ichiga olsin."
        ),
    },
    {
        'title': "Oziq-ovqat xavfsizligi siyosati",
        'doc_type': 'quality_policy',
        'standard': 'iso22000',
        'ai_prompt': (
            "ISO 22000:2018 talablariga mos oziq-ovqat xavfsizligi siyosatini yoz. "
            "HACCP tamoyillari, xavflarni boshqarish, yetkazib beruvchilar bilan ishlash "
            "va doimiy yaxshilash majburiyatini aks ettirsin."
        ),
    },
    {
        'title': 'Atrof-muhit siyosati',
        'doc_type': 'quality_policy',
        'standard': 'iso14001',
        'ai_prompt': (
            "ISO 14001:2015 talablariga mos atrof-muhit siyosatini yoz. "
            "Atrof-muhitni muhofaza qilish, ifloslanishni oldini olish, qonuniy talablarga rioya qilish "
            "va doimiy yaxshilash majburiyatlarini o'z ichiga olsin."
        ),
    },
    {
        'title': 'Mehnat xavfsizligi siyosati',
        'doc_type': 'quality_policy',
        'standard': 'iso45001',
        'ai_prompt': (
            "ISO 45001:2018 talablariga mos mehnat xavfsizligi va sog'liqni saqlash siyosatini yoz. "
            "Xavfsiz ish muhiti yaratish, xodimlarni himoya qilish, xavflarni boshqarish "
            "va ishtirok etish majburiyatlarini aks ettirsin."
        ),
    },
]

ISO9001_STEPS = [
    (1, 'Dastlabki gap tahlil',
     'Joriy holat va ISO 9001 talablari orasidagi farqlarni aniqlash',
     10, 'Gap tahlil hisoboti'),
    (2, 'Rahbariyat bilan ishlash',
     "Yuqori rahbariyatni QMS ga jalb etish, mas'uliyatlarni belgilash",
     5, "Rahbariyat majburiyati bayonnomasi"),
    (3, 'Hujjatlashtirish',
     "Sifat siyosati, protseduralar, ko'rsatmalar va shakllar tayyorlash",
     30, "QMS hujjatlar to'plami"),
    (4, 'Xodimlar tayyorlash',
     "ISO 9001 talablari bo'yicha treninglar o'tkazish",
     14, 'Trening protokollari'),
    (5, 'Joriy etish',
     'QMS ni amaliyotga joriy etish, monitoring va kuzatish',
     30, 'Joriy etish hisoboti'),
    (6, 'Ichki audit',
     "Birinchi ichki audit o'tkazish, nomuvofiqliklarni aniqlash",
     7, 'Audit hisoboti'),
    (7, 'Menejment sharhi',
     "Rahbariyat bilan natijalar ko'rib chiqish va tuzatuvchi choralar",
     3, 'Sharh bayonnomasi'),
    (8, 'Sertifikatsiya auditi',
     "Akkreditatsiyalangan organ tomonidan tashqi audit",
     5, 'ISO 9001 Sertifikat'),
    (9, 'Kuzatuv va yaxshilash',
     "Doimiy monitoring, nomuvofiqliklar kuzatuvi va yillik audit",
     16, 'Monitoring hisobotlari'),
]

ISO22000_STEPS = [
    (1, 'Dastlabki tahlil', "Oziq-ovqat xavfsizligi holati va PRPs baholash", 7, 'Tahlil hisoboti'),
    (2, 'HACCP guruhi', "Guruh tashkil etish va o'qitish", 5, "Guruh ro'yxati"),
    (3, 'Mahsulot tavsifi', "Mahsulotlar va mo'ljallangan foydalanish hujjatlash", 7, 'Mahsulot kartalari'),
    (4, 'Xavflar tahlili', "Barcha xavflarni aniqlash va baholash", 14, 'Xavflar jadvali'),
    (5, 'Nazorat choralari', "CCP va OPRP larni belgilash", 10, 'Nazorat reja'),
    (6, 'Hujjatlashtirish', "FSMS hujjatlarini tayyorlash", 21, "Hujjatlar to'plami"),
    (7, 'Joriy etish', "Tizimni amaliyotga joriy etish", 21, 'Joriy etish hisoboti'),
    (8, 'Tasdiqlash va audit', "Ichki audit va tasdiqlash faoliyatlari", 7, 'Audit hisoboti'),
    (9, 'Sertifikatsiya', "Tashqi sertifikatsiya auditi", 5, 'ISO 22000 Sertifikat'),
]


class Command(BaseCommand):
    help = 'Load starter document templates and project templates for Expert Tools'

    def handle(self, *args, **kwargs):
        # Document templates
        DocumentTemplate.objects.all().delete()
        for t in DOCUMENT_TEMPLATES:
            DocumentTemplate.objects.create(
                title=t['title'],
                doc_type=t['doc_type'],
                standard=t['standard'],
                template_content=t['ai_prompt'],
                ai_prompt=t['ai_prompt'],
            )
        self.stdout.write(
            self.style.SUCCESS(f"  {len(DOCUMENT_TEMPLATES)} ta hujjat shabloni yaratildi")
        )

        # Project templates
        ProjectTemplate.objects.all().delete()

        # ISO 9001
        iso9001 = ProjectTemplate.objects.create(
            title='ISO 9001:2015 — Standart loyiha rejasi',
            standard='iso9001',
            description='ISO 9001:2015 sertifikatiga tayyorgarlik uchun to\'liq reja (120 kun)',
            total_days=120,
        )
        for order, title, desc, days, deliverable in ISO9001_STEPS:
            ProjectTemplateStep.objects.create(
                template=iso9001, title=title, description=desc,
                duration_days=days, order=order, deliverable=deliverable,
            )

        # ISO 22000
        iso22000 = ProjectTemplate.objects.create(
            title='ISO 22000:2018 — Oziq-ovqat xavfsizligi loyiha rejasi',
            standard='iso22000',
            description="ISO 22000:2018 FSMS sertifikatiga tayyorgarlik rejasi (90 kun)",
            total_days=90,
        )
        for order, title, desc, days, deliverable in ISO22000_STEPS:
            ProjectTemplateStep.objects.create(
                template=iso22000, title=title, description=desc,
                duration_days=days, order=order, deliverable=deliverable,
            )

        self.stdout.write(self.style.SUCCESS("  2 ta loyiha shabloni yaratildi (ISO 9001, ISO 22000)"))
        self.stdout.write(self.style.SUCCESS("\nload_expert_templates muvaffaqiyatli tugadi."))
