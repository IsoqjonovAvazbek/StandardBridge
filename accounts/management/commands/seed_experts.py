"""
Management command: seed_experts

Har bir O'zbekiston viloyati uchun bitta demo (tasdiqlangan) mutaxassis yaratadi.
Idempotent — mavjud username bo'lsa qayta yaratmaydi.

    python manage.py seed_experts

Demo loginlar: expert_<region>, parol: demo12345
"""
from decimal import Decimal
from django.core.management.base import BaseCommand
from django.utils import timezone
from accounts.models import CustomUser, ExpertProfile


# (region_kod, ko'rinadigan ism, familiya, viloyat nomi)
EXPERTS = [
    ('toshkent', 'Aziz', 'Karimov', 'Toshkent'),
    ('samarqand', 'Bobur', 'Mirzayev', 'Samarqand'),
    ('buxoro', 'Davron', 'Toshev', 'Buxoro'),
    ('fargona', 'Eldor', 'Yusupov', "Farg'ona"),
    ('andijon', 'Farrux', 'Aliyev', 'Andijon'),
    ('namangan', 'Gʻayrat', 'Soliyev', 'Namangan'),
    ('xorazm', 'Hasan', 'Ortiqov', 'Xorazm'),
    ('qashqadaryo', 'Islom', 'Rahimov', 'Qashqadaryo'),
    ('surxondaryo', 'Jasur', 'Berdiyev', 'Surxondaryo'),
    ('navoiy', 'Kamol', 'Ziyodov', 'Navoiy'),
    ('jizzax', 'Laziz', 'Umarov', 'Jizzax'),
    ('sirdaryo', 'Murod', 'Qodirov', 'Sirdaryo'),
    ('qoraqalpogiston', 'Nodir', 'Sapayev', "Qoraqalpog'iston"),
]

SPECIALIZATIONS = [
    'ISO 9001, ISO 22000',
    'ISO 14001, ISO 45001',
    'ISO 9001, ISO 14001',
    'ISO 22000, HACCP',
    'ISO 9001, ISO 45001',
]

# standard_tags — qidiruv filtri uchun (ExpertProfile.standard_tags JSONField)
STANDARD_TAGS = [
    ['iso9001', 'iso22000'],
    ['iso14001', 'iso45001'],
    ['iso9001', 'iso14001'],
    ['iso22000'],
    ['iso9001', 'iso45001'],
]


class Command(BaseCommand):
    help = 'Har viloyat uchun bitta demo tasdiqlangan mutaxassis yaratadi'

    def handle(self, *args, **options):
        created = 0
        for i, (region, first, last, region_name) in enumerate(EXPERTS):
            username = f'expert_{region}'
            if CustomUser.objects.filter(username=username).exists():
                continue

            user = CustomUser.objects.create_user(
                username=username,
                email=f'{username}@demo.uz',
                password='demo12345',
                first_name=first,
                last_name=last,
                role='expert',
                region=region,
                company_name=f'{region_name} Sertifikatsiya Markazi',
            )
            ExpertProfile.objects.create(
                user=user,
                bio=f'{region_name} viloyatida {5 + i % 8} yillik tajribaga ega ISO sertifikatsiya mutaxassisi.',
                specializations=SPECIALIZATIONS[i % len(SPECIALIZATIONS)],
                standard_tags=STANDARD_TAGS[i % len(STANDARD_TAGS)],
                experience_years=5 + i % 8,
                rating=Decimal('4.5') + Decimal('0.1') * (i % 5),
                total_projects=10 + i * 3,
                is_available=True,
                is_verified=True,
                verified_at=timezone.now(),
                hourly_rate=Decimal('5.00'),
                region=region,
                project_price=Decimal('1000') + Decimal('200') * (i % 6),
                completion_days=60 + (i % 4) * 15,
                phone=f'+99890{1000000 + i}',
            )
            created += 1
            self.stdout.write(f'  + {username} ({region_name})')

        self.stdout.write(self.style.SUCCESS(
            f'{created} ta demo mutaxassis yaratildi. '
            f'(Jami expert: {CustomUser.objects.filter(role="expert").count()})'
        ))
