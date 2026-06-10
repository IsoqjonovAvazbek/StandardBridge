"""
Management command: seed_data

Industry (sanoat) va Standard (standartlar) ma'lumotlarini yuklaydi.
Idempotent — get_or_create ishlatadi, qayta ishga tushirsa dublikat yaratmaydi.

    python manage.py seed_data
"""
from django.core.management.base import BaseCommand
from analysis.models import Industry, Standard


INDUSTRIES = [
    # (name, name_ru, name_en, icon, order)
    ("To'qimachilik",    'Текстиль',             'Textile',              'shirt',  1),
    ('Oziq-ovqat',       'Продукты питания',      'Food & Beverage',      'apple',  2),
    ('Kimyo',            'Химическая',            'Chemical',             'flask',  3),
    ('Mashinasozlik',    'Машиностроение',         'Mechanical Eng.',      'tool',   4),
    ('Qurilish',         'Строительство',          'Construction',         'home',   5),
    ('Farmatsevtika',    'Фармацевтика',           'Pharmaceuticals',      '💊',     6),
    ("Qishloq xo'jaligi", 'Сельское хозяйство',   'Agriculture',          '🌾',     7),
    ('Elektrotexnika',   'Электротехника',         'Electrical Eng.',      '⚡',     8),
    ('Yengil sanoat',    'Лёгкая промышленность', 'Light Industry',       '👗',     9),
    ('Metallurgiya',     'Металлургия',            'Metallurgy',           '⚙️',    10),
    ('Neft va gaz',      'Нефть и газ',            'Oil & Gas',            '🛢️',   11),
]

# (code, name, name_ru, name_en, type, industry_name)
STANDARDS = [
    ('UzDST ISO 9001',
     'Sifat menejmenti tizimi (UzDST)',
     'Система менеджмента качества (UzDST)',
     'Quality Management System (UzDST)',
     'local', "To'qimachilik"),
    ('ISO 9001',
     'Sifat menejmenti tizimi',
     'Система менеджмента качества',
     'Quality Management System',
     'international', "To'qimachilik"),
    ('UzDST ISO 22000',
     'Oziq-ovqat xavfsizligi (UzDST)',
     'Безопасность пищевых продуктов (UzDST)',
     'Food Safety (UzDST)',
     'local', 'Oziq-ovqat'),
    ('ISO 22000',
     'Oziq-ovqat xavfsizligi menejmenti',
     'Менеджмент безопасности пищевой продукции',
     'Food Safety Management',
     'international', 'Oziq-ovqat'),
    ('GOST 12.0.001',
     'Mehnat xavfsizligi (GOST)',
     'Безопасность труда (ГОСТ)',
     'Occupational Safety (GOST)',
     'local', 'Mashinasozlik'),
    ('ISO 45001',
     'Mehnat xavfsizligi va salomatligi',
     'Охрана здоровья и безопасность труда',
     'Occupational Health & Safety',
     'international', 'Mashinasozlik'),
    ('UzDST ISO 14001',
     'Atrof-muhit menejmenti (UzDST)',
     'Экологический менеджмент (UzDST)',
     'Environmental Management (UzDST)',
     'local', 'Kimyo'),
    ('ISO 14001',
     'Atrof-muhit menejmenti tizimi',
     'Система экологического менеджмента',
     'Environmental Management System',
     'international', 'Kimyo'),
]


class Command(BaseCommand):
    help = 'Sanoat va standartlarni yuklaydi (idempotent)'

    def handle(self, *args, **options):
        ind_count = 0
        for name, name_ru, name_en, icon, order in INDUSTRIES:
            obj, created = Industry.objects.get_or_create(
                name=name,
                defaults={
                    'name_ru': name_ru,
                    'name_en': name_en,
                    'icon': icon,
                    'order': order,
                    'is_active': True,
                },
            )
            if not created:
                updated = False
                if not obj.name_ru:
                    obj.name_ru = name_ru
                    updated = True
                if not obj.name_en:
                    obj.name_en = name_en
                    updated = True
                if updated:
                    obj.save(update_fields=['name_ru', 'name_en'])
            else:
                ind_count += 1

        std_count = 0
        for code, name, name_ru, name_en, type_, industry_name in STANDARDS:
            industry = Industry.objects.filter(name=industry_name).first()
            obj, created = Standard.objects.get_or_create(
                code=code,
                defaults={
                    'name': name,
                    'name_ru': name_ru,
                    'name_en': name_en,
                    'type': type_,
                    'industry': industry,
                    'is_active': True,
                },
            )
            if not created:
                updated = False
                if not obj.name:
                    obj.name = name
                    updated = True
                if not obj.name_ru:
                    obj.name_ru = name_ru
                    updated = True
                if not obj.name_en:
                    obj.name_en = name_en
                    updated = True
                if updated:
                    obj.save(update_fields=[f for f in ['name', 'name_ru', 'name_en'] if updated])
            else:
                std_count += 1

        self.stdout.write(self.style.SUCCESS(
            f'{ind_count} ta yangi sanoat, {std_count} ta yangi standart yuklandi. '
            f'(Jami: {Industry.objects.count()} sanoat, {Standard.objects.count()} standart)'
        ))
