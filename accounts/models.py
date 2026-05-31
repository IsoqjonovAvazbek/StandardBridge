from django.contrib.auth.models import AbstractUser
from django.db import models
import uuid


class CustomUser(AbstractUser):
    ROLE_CHOICES = [
        ('entrepreneur', 'Tadbirkor'),
        ('expert', 'Mutaxassis'),
        ('admin', 'Admin'),
    ]

    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='entrepreneur')
    company_name = models.CharField(max_length=200, blank=True)
    phone = models.CharField(max_length=20, blank=True)
    region = models.CharField(max_length=100, blank=True)
    industry = models.CharField(max_length=100, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    # Referral
    referral_code = models.CharField(max_length=12, unique=True, blank=True)
    referred_by = models.ForeignKey(
        'self', on_delete=models.SET_NULL, null=True, blank=True, related_name='referrals'
    )

    def save(self, *args, **kwargs):
        if not self.referral_code:
            self.referral_code = uuid.uuid4().hex[:8].upper()
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

    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name='expert_profile')
    bio = models.TextField(blank=True)
    specializations = models.CharField(max_length=500, blank=True)
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

class EntrepreneurProfile(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name='entrepreneur_profile')
    company_description = models.TextField(blank=True)
    employee_count = models.IntegerField(default=0)
    annual_revenue = models.CharField(max_length=100, blank=True)
    export_experience = models.BooleanField(default=False)
    target_markets = models.CharField(max_length=500, blank=True)
    
    def __str__(self):
        return f"Tadbirkor: {self.user.company_name}"