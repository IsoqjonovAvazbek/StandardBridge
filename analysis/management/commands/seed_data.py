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

# (code, type, industry_name)
STANDARDS = [
    ('UzDST ISO 9001', 'local', "To'qimachilik"),
    ('ISO 9001', 'international', "To'qimachilik"),
    ('UzDST ISO 22000', 'local', 'Oziq-ovqat'),
    ('ISO 22000', 'international', 'Oziq-ovqat'),
    ('GOST 12.0.001', 'local', 'Mashinasozlik'),
    ('ISO 45001', 'international', 'Mashinasozlik'),
    ('UzDST ISO 14001', 'local', 'Kimyo'),
    ('ISO 14001', 'international', 'Kimyo'),
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
        for code, type_, industry_name in STANDARDS:
            industry = Industry.objects.filter(name=industry_name).first()
            obj, created = Standard.objects.get_or_create(
                code=code,
                defaults={'type': type_, 'industry': industry, 'is_active': True},
            )
            if created:
                std_count += 1

        self.stdout.write(self.style.SUCCESS(
            f'{ind_count} ta yangi sanoat, {std_count} ta yangi standart yuklandi. '
            f'(Jami: {Industry.objects.count()} sanoat, {Standard.objects.count()} standart)'
        ))
