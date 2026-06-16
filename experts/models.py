from django.db import models
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal
from accounts.models import CustomUser
from analysis.models import GapAnalysis


class Project(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Taklif yuborildi'),
        ('negotiating', 'Narx kelishilmoqda'),
        ('accepted', 'Qabul qilindi'),
        ('in_progress', 'Jarayonda'),
        ('review', 'Tekshiruvda'),
        ('completed', 'Bajarildi'),
        ('cancelled', 'Bekor qilindi'),
    ]

    SLA_STATUS_CHOICES = [
        ('on_time', 'Vaqtida'),
        ('warning', 'Ogohlantirish'),
        ('breached', 'Muddat o\'tdi'),
    ]

    analysis = models.ForeignKey(GapAnalysis, on_delete=models.CASCADE, related_name='projects')
    entrepreneur = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='entrepreneur_projects')
    expert = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, blank=True, related_name='expert_projects')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    expert_price = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    expert_days = models.IntegerField(default=0)
    platform_fee = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    expert_payment = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    entrepreneur_message = models.TextField(blank=True)
    expert_message = models.TextField(blank=True)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    review_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # SLA fields
    sla_hours = models.IntegerField(default=72)  # mutaxassis qabul qilish muddati
    sla_deadline = models.DateTimeField(null=True, blank=True)
    sla_status = models.CharField(max_length=20, choices=SLA_STATUS_CHOICES, default='on_time')

    # Ish bajarish muddati (to'lovdan keyin expert_days ga qarab hisoblanadi)
    work_deadline = models.DateTimeField(null=True, blank=True)

    # Qarshi taklif (entrepreneur → expert)
    COUNTER_STATUS_CHOICES = [
        ('none',     'Yo\'q'),
        ('pending',  'Kutilmoqda'),
        ('accepted', 'Qabul qilindi'),
        ('rejected', 'Rad etildi'),
    ]
    counter_price = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    counter_message = models.TextField(blank=True)
    counter_status = models.CharField(max_length=20, choices=COUNTER_STATUS_CHOICES, default='none')
    counter_rounds = models.PositiveSmallIntegerField(default=0)

    def save(self, *args, **kwargs):
        if self.expert_price:
            self.platform_fee = self.expert_price * Decimal('0.20')
            self.expert_payment = self.expert_price * Decimal('0.80')
        # Auto-set SLA deadline on first save (when created_at not yet set)
        if not self.pk and not self.sla_deadline:
            self.sla_deadline = timezone.now() + timedelta(hours=self.sla_hours)
        super().save(*args, **kwargs)

    @property
    def sla_hours_left(self):
        """Returns hours remaining until SLA deadline. Negative if breached."""
        if not self.sla_deadline:
            return None
        delta = self.sla_deadline - timezone.now()
        return delta.total_seconds() / 3600

    @property
    def sla_is_active(self):
        """SLA only applies while project is pending (awaiting expert response)."""
        return self.status == 'pending'

    def update_sla_status(self):
        """Recalculate sla_status based on current time. Call before save."""
        if not self.sla_deadline or not self.sla_is_active:
            return
        hours_left = self.sla_hours_left
        if hours_left is None:
            return
        if hours_left <= 0:
            self.sla_status = 'breached'
        elif hours_left <= 24:
            self.sla_status = 'warning'
        else:
            self.sla_status = 'on_time'

    @property
    def work_days_left(self):
        """Ish bajarish muddatigacha qolgan kunlar (manfiy = kechikkan)."""
        if not self.work_deadline:
            return None
        delta = self.work_deadline - timezone.now()
        return int(delta.total_seconds() / 86400)

    @property
    def work_sla_status(self):
        """on_time / warning (≤2 kun) / overdue."""
        if not self.work_deadline or self.status not in ('in_progress', 'review'):
            return None
        days = self.work_days_left
        if days is None:
            return None
        if days < 0:
            return 'overdue'
        if days <= 2:
            return 'warning'
        return 'on_time'

    def __str__(self):
        return f"Loyiha #{self.pk} — {self.entrepreneur}"


class ProjectUpdate(models.Model):
    TYPE_CHOICES = [
        ('message', 'Xabar'),
        ('progress', 'Progress'),
        ('document', 'Hujjat'),
        ('completed', 'Yakunlandi'),
    ]

    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='updates')
    author = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    message = models.TextField(blank=True)
    update_type = models.CharField(max_length=20, choices=TYPE_CHOICES, default='message')
    file = models.FileField(upload_to='chat_files/', blank=True, null=True)
    file_name = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.project} — {self.author}"


class Document(models.Model):
    DOC_TYPE_CHOICES = [
        ('template', 'Shablon'),
        ('filled', 'To\'ldirilgan'),
        ('certificate', 'Sertifikat'),
        ('report', 'Hisobot'),
    ]

    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='documents')
    uploaded_by = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    title = models.CharField(max_length=300)
    doc_type = models.CharField(max_length=20, choices=DOC_TYPE_CHOICES, default='template')
    file = models.FileField(upload_to='documents/')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.title} ({self.get_doc_type_display()})"


class Review(models.Model):
    project = models.OneToOneField(Project, on_delete=models.CASCADE, related_name='review')
    entrepreneur = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='given_reviews')
    expert = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='received_reviews')
    rating = models.IntegerField(default=5)
    comment = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Baho {self.rating}/5 — {self.expert.get_full_name()}"


class Notification(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='notifications')
    title = models.CharField(max_length=200)
    message = models.TextField()
    link = models.CharField(max_length=500, blank=True, default='')
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.title} — {self.user.username}"


class Payment(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Kutilmoqda'),
        ('held', 'Ushlab turilgan'),
        ('released', 'Mutaxassisga o\'tkazildi'),
        ('refunded', 'Qaytarildi'),
    ]

    project = models.OneToOneField(Project, on_delete=models.CASCADE, related_name='payment')
    entrepreneur = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='payments')
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    platform_fee = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    expert_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    payme_transaction_id = models.CharField(max_length=200, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    paid_at = models.DateTimeField(null=True, blank=True)
    released_at = models.DateTimeField(null=True, blank=True)

    def save(self, *args, **kwargs):
        from decimal import Decimal as _D
        self.platform_fee = (self.amount * _D('0.20')).quantize(_D('0.01'))
        self.expert_amount = self.amount - self.platform_fee
        super().save(*args, **kwargs)

    def __str__(self):
        return f"To'lov #{self.pk} — {self.status}"


class Wallet(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name='wallet')
    balance = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    card_number = models.CharField(max_length=20, blank=True)
    card_holder = models.CharField(max_length=100, blank=True)
    card_expiry = models.CharField(max_length=10, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Hamyon — {self.user.get_full_name()} (${self.balance})"


class WithdrawalRequest(models.Model):
    """Expert requests to withdraw funds from wallet to their card."""
    STATUS_CHOICES = [
        ('pending', 'Kutilmoqda'),
        ('approved', 'Tasdiqlandi'),
        ('rejected', "Rad etildi"),
    ]
    wallet = models.ForeignKey(Wallet, on_delete=models.CASCADE, related_name='withdrawal_requests')
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    # Fernet bilan shifrlangan karta raqami (max_length=500 — shifrlangan qiymat ~120 bayt)
    card_number = models.CharField(max_length=500)
    card_holder = models.CharField(max_length=100, blank=True)
    note = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    admin_note = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    processed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']

    @property
    def card_number_plain(self):
        """Shifrlangan karta raqamini ochiq ko'rinishda qaytaradi."""
        from .crypto import decrypt_card
        return decrypt_card(self.card_number)

    def __str__(self):
        return f"Chiqim ${self.amount} — {self.wallet.user.get_full_name()} ({self.status})"


class WalletTransaction(models.Model):
    TYPE_CHOICES = [
        ('income', 'Kirim'),
        ('withdrawal', 'Chiqim'),
        ('refund', 'Qaytarish'),
    ]

    wallet = models.ForeignKey(Wallet, on_delete=models.CASCADE, related_name='transactions')
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    transaction_type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    description = models.CharField(max_length=300)
    project = models.ForeignKey(Project, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.get_transaction_type_display()} ${self.amount} — {self.wallet.user.get_full_name()}"


class ScopeRequest(models.Model):
    """Expert sends additional scope request when real work is larger than analyzed gaps."""
    STATUS_CHOICES = [
        ('pending',  'Javob kutilmoqda'),
        ('accepted', 'Qabul qilindi'),
        ('rejected', 'Rad etildi'),
    ]
    project    = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='scope_requests')
    expert     = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='sent_scope_requests')
    reason     = models.TextField()
    extra_price = models.DecimalField(max_digits=12, decimal_places=2)
    status     = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    responded_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"ScopeRequest #{self.pk} — Loyiha #{self.project_id} ({self.status})"


class Dispute(models.Model):
    """Entrepreneur can open a dispute if they are not satisfied with the work."""
    STATUS_CHOICES = [
        ('open', 'Ochiq'),
        ('in_review', "Ko'rib chiqilmoqda"),
        ('resolved', 'Hal qilindi'),
        ('closed', 'Yopildi'),
    ]
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='disputes')
    opened_by = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='opened_disputes')
    reason = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='open')
    admin_decision = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    resolved_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Nizo #{self.pk} — Loyiha #{self.project_id} ({self.status})"