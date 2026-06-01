"""
Management command: create_admin

Environment o'zgaruvchilaridan superuser/admin yaratadi (yoki yangilaydi).
Production deploy'da `createsuperuser` interaktiv bo'lgani uchun ishlatib bo'lmaydi —
shuning uchun env var orqali yaratamiz. Idempotent: mavjud bo'lsa parolni yangilaydi.

Kerakli env var'lar:
    ADMIN_USERNAME, ADMIN_PASSWORD (majburiy)
    ADMIN_EMAIL (ixtiyoriy)

    python manage.py create_admin
"""
import os
from django.core.management.base import BaseCommand
from accounts.models import CustomUser


class Command(BaseCommand):
    help = "Env var'lardan admin (superuser) yaratadi yoki parolini yangilaydi"

    def handle(self, *args, **options):
        username = os.environ.get('ADMIN_USERNAME', '').strip()
        password = os.environ.get('ADMIN_PASSWORD', '').strip()
        email = os.environ.get('ADMIN_EMAIL', '').strip()

        if not username or not password:
            self.stdout.write(self.style.WARNING(
                'ADMIN_USERNAME yoki ADMIN_PASSWORD o\'rnatilmagan — admin yaratilmadi.'
            ))
            return

        user, created = CustomUser.objects.get_or_create(
            username=username,
            defaults={'email': email, 'role': 'admin'},
        )
        user.email = email or user.email
        user.role = 'admin'
        user.is_staff = True
        user.is_superuser = True
        user.set_password(password)
        user.save()

        if created:
            self.stdout.write(self.style.SUCCESS(f'Admin "{username}" yaratildi.'))
        else:
            self.stdout.write(self.style.SUCCESS(f'Admin "{username}" yangilandi (parol o\'rnatildi).'))
