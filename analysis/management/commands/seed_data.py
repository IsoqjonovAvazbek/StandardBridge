"""
Management command: seed_data

Industry (sanoat) va Standard (standartlar) ma'lumotlarini yuklaydi.
Idempotent — get_or_create ishlatadi, qayta ishga tushirsa dublikat yaratmaydi.

    python manage.py seed_data
"""
from django.core.management.base import BaseCommand
from analysis.models import Industry, Standard


INDUSTRIES = [
    # (name, icon, order)
    ("To'qimachilik", 'shirt', 1),
    ('Oziq-ovqat', 'apple', 2),
    ('Kimyo', 'flask', 3),
    ('Mashinasozlik', 'tool', 4),
    ('Qurilish', 'home', 5),
    ('Farmatsevtika', '💊', 6),
    ("Qishloq xo'jaligi", '🌾', 7),
    ('Elektrotexnika', '⚡', 8),
    ('Yengil sanoat', '👗', 9),
    ('Metallurgiya', '⚙️', 10),
    ('Neft va gaz', '🛢️', 11),
]

# (code, name, type, industry_name)
STANDARDS = [
    ('UzDST ISO 9001', 'Sifat menejmenti tizimi (UzDST)', 'local', "To'qimachilik"),
    ('ISO 9001', 'Sifat menejmenti tizimi', 'international', "To'qimachilik"),
    ('UzDST ISO 22000', 'Oziq-ovqat xavfsizligi (UzDST)', 'local', 'Oziq-ovqat'),
    ('ISO 22000', 'Oziq-ovqat xavfsizligi menejmenti', 'international', 'Oziq-ovqat'),
    ('GOST 12.0.001', 'Mehnat xavfsizligi (GOST)', 'local', 'Mashinasozlik'),
    ('ISO 45001', 'Mehnat xavfsizligi va salomatligi', 'international', 'Mashinasozlik'),
    ('UzDST ISO 14001', 'Atrof-muhit menejmenti (UzDST)', 'local', 'Kimyo'),
    ('ISO 14001', 'Atrof-muhit menejmenti tizimi', 'international', 'Kimyo'),
]


class Command(BaseCommand):
    help = 'Sanoat va standartlarni yuklaydi (idempotent)'

    def handle(self, *args, **options):
        ind_count = 0
        for name, icon, order in INDUSTRIES:
            obj, created = Industry.objects.get_or_create(
                name=name,
                defaults={'icon': icon, 'order': order, 'is_active': True},
            )
            if created:
                ind_count += 1

        std_count = 0
        for code, name, type_, industry_name in STANDARDS:
            industry = Industry.objects.filter(name=industry_name).first()
            obj, created = Standard.objects.get_or_create(
                code=code,
                defaults={'name': name, 'type': type_, 'industry': industry, 'is_active': True},
            )
            if not created and not obj.name:
                obj.name = name
                obj.save(update_fields=['name'])
            if created:
                std_count += 1

        self.stdout.write(self.style.SUCCESS(
            f'{ind_count} ta yangi sanoat, {std_count} ta yangi standart yuklandi. '
            f'(Jami: {Industry.objects.count()} sanoat, {Standard.objects.count()} standart)'
        ))
