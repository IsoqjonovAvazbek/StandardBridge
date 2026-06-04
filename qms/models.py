from django.db import models
from django.utils import timezone
from accounts.models import CustomUser


class ChecklistItem(models.Model):
    STANDARD_CHOICES = [
        ('iso9001', 'ISO 9001'),
        ('iso22000', 'ISO 22000'),
        ('iso14001', 'ISO 14001'),
        ('iso45001', 'ISO 45001'),
    ]
    standard = models.CharField(max_length=20, choices=STANDARD_CHOICES)
    clause = models.CharField(max_length=20, blank=True, help_text='ISO clause number, e.g. 4.1, 6.2.2')
    question = models.TextField()
    requirement = models.TextField(blank=True)
    order = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['standard', 'order']

    def __str__(self):
        return f"[{self.standard}] {self.question[:60]}"


class ChecklistResponse(models.Model):
    STATUS_CHOICES = [
        ('compliant', 'Mos'),
        ('partial', 'Qisman'),
        ('non_compliant', 'Mos emas'),
        ('not_checked', 'Tekshirilmagan'),
    ]
    company = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='checklist_responses')
    item = models.ForeignKey(ChecklistItem, on_delete=models.CASCADE, related_name='responses')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='not_checked')
    note = models.TextField(blank=True)
    evidence_text = models.TextField(blank=True, help_text='Evidence: document name, link, or description')
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['company', 'item']

    def __str__(self):
        return f"{self.company.company_name} — {self.item_id} — {self.status}"


class QMSDocument(models.Model):
    DOC_TYPE_CHOICES = [
        ('policy', 'Siyosat'),
        ('procedure', 'Protsedura'),
        ('instruction', "Ko'rsatma"),
        ('record', 'Yozuv'),
        ('certificate', 'Sertifikat'),
    ]
    company = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='qms_documents')
    title = models.CharField(max_length=300)
    doc_type = models.CharField(max_length=20, choices=DOC_TYPE_CHOICES)
    file = models.FileField(upload_to='qms_documents/', blank=True)
    version = models.CharField(max_length=20, default='1.0')
    uploaded_at = models.DateTimeField(auto_now_add=True)
    expiry_date = models.DateField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    expiry_notified = models.BooleanField(default=False, help_text='Muddat eslatmasi yuborilganmi')
    ai_content = models.TextField(blank=True, help_text='AI tomonidan yaratilgan hujjat matni (markdown)')

    class Meta:
        ordering = ['-uploaded_at']

    def __str__(self):
        return f"{self.title} v{self.version}"

    @property
    def is_expired(self):
        return self.expiry_date is not None and self.expiry_date < timezone.now().date()

    @property
    def days_to_expiry(self):
        if self.expiry_date is None:
            return None
        return (self.expiry_date - timezone.now().date()).days


class QMSDocumentVersion(models.Model):
    """Keeps older versions when a document is updated."""
    document = models.ForeignKey(QMSDocument, on_delete=models.CASCADE, related_name='version_history')
    version = models.CharField(max_length=20)
    file = models.FileField(upload_to='qms_documents/history/')
    note = models.TextField(blank=True, help_text="O'zgarishlar tavsifi")
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.document.title} v{self.version} ({self.created_at:%d.%m.%Y})"


class NonConformity(models.Model):
    SEVERITY_CHOICES = [
        ('minor', 'Kichik'),
        ('major', 'Katta'),
        ('critical', 'Kritik'),
    ]
    STATUS_CHOICES = [
        ('open', 'Ochiq'),
        ('in_progress', 'Jarayonda'),
        ('closed', 'Yopilgan'),
    ]
    company = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='nonconformities')
    code = models.CharField(max_length=30, blank=True, help_text='Izlanadigan raqam, masalan NC-2026-001')
    title = models.CharField(max_length=300)
    description = models.TextField()
    severity = models.CharField(max_length=20, choices=SEVERITY_CHOICES)
    assigned_to = models.CharField(max_length=200, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='open')
    due_date = models.DateField(null=True, blank=True)
    root_cause = models.TextField(blank=True)
    corrective_action = models.TextField(blank=True)
    ai_suggestion = models.TextField(blank=True, help_text='AI taklif qilgan tub sabab va tuzatuvchi chora')
    is_effective_verified = models.BooleanField(default=False, help_text='Tuzatuvchi chora samarali bo\'lganmi?')
    verification_note = models.TextField(blank=True)
    verified_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    closed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.code or self.title} [{self.severity}] — {self.status}"

    @property
    def is_overdue(self):
        return (
            self.due_date is not None
            and self.status != 'closed'
            and self.due_date < timezone.now().date()
        )


class RiskItem(models.Model):
    STANDARD_CHOICES = [
        ('iso9001', 'ISO 9001'),
        ('iso14001', 'ISO 14001'),
        ('iso45001', 'ISO 45001'),
        ('iso22000', 'ISO 22000'),
    ]
    LIKELIHOOD_CHOICES = [(i, str(i)) for i in range(1, 6)]
    IMPACT_CHOICES = [(i, str(i)) for i in range(1, 6)]
    STATUS_CHOICES = [
        ('open', 'Ochiq'),
        ('mitigated', 'Kamaytarilgan'),
        ('accepted', 'Qabul qilingan'),
        ('closed', 'Yopilgan'),
    ]

    company = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='risk_items')
    standard = models.CharField(max_length=20, choices=STANDARD_CHOICES, default='iso9001')
    process_area = models.CharField(max_length=200, help_text="Jarayon yoki bo'lim nomi")
    description = models.TextField(help_text='Risk tavsifi')
    likelihood = models.IntegerField(choices=LIKELIHOOD_CHOICES, default=3)
    impact = models.IntegerField(choices=IMPACT_CHOICES, default=3)
    mitigation = models.TextField(blank=True, help_text='Riskni kamaytirish choralari')
    owner = models.CharField(max_length=200, blank=True, help_text='Masul shaxs')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='open')
    due_date = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"[{self.get_standard_display()}] {self.process_area} — risk_score={self.risk_score}"

    @property
    def risk_score(self):
        return self.likelihood * self.impact

    @property
    def risk_level(self):
        s = self.risk_score
        if s >= 15:
            return 'critical'
        if s >= 9:
            return 'high'
        if s >= 4:
            return 'medium'
        return 'low'

    @property
    def is_overdue(self):
        return (
            self.due_date is not None
            and self.status not in ('closed',)
            and self.due_date < timezone.now().date()
        )


class TrainingRecord(models.Model):
    company = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='training_records')
    employee_name = models.CharField(max_length=200)
    position = models.CharField(max_length=200, blank=True)
    training_name = models.CharField(max_length=300)
    standard_clause = models.CharField(max_length=100, blank=True, help_text='Masalan: ISO 9001 7.2')
    date_completed = models.DateField()
    trainer = models.CharField(max_length=200, blank=True)
    certificate_number = models.CharField(max_length=100, blank=True)
    expiry_date = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-date_completed']

    def __str__(self):
        return f"{self.employee_name} — {self.training_name}"

    @property
    def is_expired(self):
        return self.expiry_date is not None and self.expiry_date < timezone.now().date()

    @property
    def days_to_expiry(self):
        if self.expiry_date is None:
            return None
        return (self.expiry_date - timezone.now().date()).days


class AuditSchedule(models.Model):
    AUDIT_TYPE_CHOICES = [
        ('internal', 'Ichki audit'),
        ('external', 'Tashqi audit'),
        ('certification', 'Sertifikatsiya auditi'),
        ('surveillance', 'Nazorat auditi'),
    ]
    STATUS_CHOICES = [
        ('planned', 'Rejalashtirilgan'),
        ('in_progress', 'Jarayonda'),
        ('completed', 'Bajarildi'),
        ('cancelled', 'Bekor qilindi'),
    ]
    company = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='audit_schedules')
    audit_type = models.CharField(max_length=20, choices=AUDIT_TYPE_CHOICES)
    standard = models.CharField(max_length=50)
    planned_date = models.DateField()
    auditor_name = models.CharField(max_length=200, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='planned')
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['planned_date']

    def __str__(self):
        return f"{self.get_audit_type_display()} — {self.standard} — {self.planned_date}"

    @property
    def is_overdue(self):
        return (
            self.status in ('planned', 'in_progress')
            and self.planned_date < timezone.now().date()
        )
