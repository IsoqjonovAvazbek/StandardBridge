from django.contrib.auth.models import AbstractUser
from django.db import models
from functools import cached_property
import uuid


class CustomUser(AbstractUser):
    ROLE_CHOICES = [
        ('entrepreneur', 'Tadbirkor'),
        ('expert', 'Mutaxassis'),
        ('admin', 'Admin'),
    ]

    LANG_CHOICES = [('uz', "O'zbek"), ('ru', 'Русский'), ('en', 'English')]

    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='entrepreneur')
    company_name = models.CharField(max_length=200, blank=True)
    phone = models.CharField(max_length=20, blank=True)
    region = models.CharField(max_length=100, blank=True)
    industry = models.CharField(max_length=100, blank=True)
    preferred_language = models.CharField(max_length=5, choices=LANG_CHOICES, default='uz')
    created_at = models.DateTimeField(auto_now_add=True)

    # Avatar
    avatar = models.ImageField(upload_to='avatars/', null=True, blank=True)

    # Email verification
    is_email_verified = models.BooleanField(default=True)
    email_verify_token = models.CharField(max_length=72, blank=True, db_index=True)

    # Telegram
    telegram_chat_id = models.CharField(max_length=20, blank=True, db_index=True)
    telegram_link_token = models.CharField(max_length=64, blank=True, db_index=True)

    # Referral
    referral_code = models.CharField(max_length=12, unique=True, blank=True)
    referred_by = models.ForeignKey(
        'self', on_delete=models.SET_NULL, null=True, blank=True, related_name='referrals'
    )

    def save(self, *args, **kwargs):
        if not self.referral_code:
            for _ in range(10):
                code = uuid.uuid4().hex[:8].upper()
                if not CustomUser.objects.filter(referral_code=code).exists():
                    self.referral_code = code
                    break
            else:
                self.referral_code = uuid.uuid4().hex[:12].upper()
        super().save(*args, **kwargs)
    
    def is_entrepreneur(self):
        return self.role == 'entrepreneur'
    
    def is_expert(self):
        return self.role == 'expert'
    
    def is_admin(self):
        return self.role == 'admin'
    
    def __str__(self):
        return f"{self.get_full_name()} ({self.get_role_display()})"


class ExpertProfile(models.Model):
    REGION_CHOICES = [
        ('toshkent', 'Toshkent'),
        ('fargona', 'Farg\'ona'),
        ('samarqand', 'Samarqand'),
        ('buxoro', 'Buxoro'),
        ('andijon', 'Andijon'),
        ('namangan', 'Namangan'),
        ('qashqadaryo', 'Qashqadaryo'),
        ('surxondaryo', 'Surxondaryo'),
        ('xorazm', 'Xorazm'),
        ('navoiy', 'Navoiy'),
        ('jizzax', 'Jizzax'),
        ('sirdaryo', 'Sirdaryo'),
        ('qoraqalpogiston', 'Qoraqalpog\'iston'),
    ]

    STANDARD_CHOICES = [
        ('iso9001',    'ISO 9001'),
        ('iso14001',   'ISO 14001'),
        ('iso45001',   'ISO 45001'),
        ('iso22000',   'ISO 22000'),
        ('ce_marking', 'CE Marking'),
        ('gost_r',     'GOST R'),
        ('uzdst',      'UzDST'),
    ]

    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name='expert_profile')
    bio = models.TextField(blank=True)
    specializations = models.CharField(max_length=500, blank=True)
    # Standartlashtirilgan teglar — filter va qidiruvda ishlatiladi
    standard_tags = models.JSONField(default=list, blank=True)
    experience_years = models.IntegerField(default=0)
    rating = models.FloatField(default=0.0)
    total_projects = models.IntegerField(default=0)
    is_available = models.BooleanField(default=True)
    hourly_rate = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    region = models.CharField(max_length=50, choices=REGION_CHOICES, blank=True)
    project_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    completion_days = models.IntegerField(default=0)
    certificates = models.TextField(blank=True)
    phone = models.CharField(max_length=20, blank=True)
    is_verified = models.BooleanField(default=False)
    verified_at = models.DateTimeField(null=True, blank=True)
    # Credential / qualification fields for admin verification
    cert_number = models.CharField(max_length=100, blank=True, help_text='Sertifikat raqami (masalan: CB-2024-1234)')
    issuing_body = models.CharField(max_length=200, blank=True, help_text='Sertifikat bergan tashkilot')
    cert_expiry = models.DateField(null=True, blank=True, help_text='Sertifikat amal qilish muddati')

    _TIERS = [
        ('elite',    25, None, 12, 'Sariq',   'yellow'),
        ('premium',  10, 25,   15, 'Binafsha', 'purple'),
        ('silver',    3, 10,   18, 'Ko\'k',    'blue'),
        ('new',       0,  3,   20, 'Kulrang',  'gray'),
    ]

    @cached_property
    def tier_info(self):
        n = self.total_projects
        for key, min_p, max_p, commission, label_uz, color in self._TIERS:
            if n >= min_p:
                to_next = max(0, max_p - n) if max_p else 0
                return {
                    'key': key, 'label': label_uz, 'color': color,
                    'commission': commission, 'to_next': to_next,
                    'max_p': max_p, 'min_p': min_p,
                }
        return {'key': 'new', 'label': 'Yangi', 'color': 'gray', 'commission': 20, 'to_next': 3}

class EntrepreneurProfile(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name='entrepreneur_profile')
    company_description = models.TextField(blank=True)
    employee_count = models.IntegerField(default=0)
    annual_revenue = models.CharField(max_length=100, blank=True)
    export_experience = models.BooleanField(default=False)
    target_markets = models.CharField(max_length=500, blank=True)
    
    def __str__(self):
        return f"Tadbirkor: {self.user.company_name}"