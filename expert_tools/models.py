from django.db import models
from accounts.models import CustomUser
from experts.models import Project


class DocumentTemplate(models.Model):
    DOC_TYPE_CHOICES = [
        ('quality_policy', 'Sifat siyosati'),
        ('procedure', 'Protsedura'),
        ('instruction', "Ish ko'rsatmasi"),
        ('audit_report', 'Audit hisoboti'),
        ('corrective_action', 'Tuzatuvchi chora'),
        ('management_review', 'Menejment sharhi'),
    ]
    STANDARD_CHOICES = [
        ('iso9001', 'ISO 9001'),
        ('iso22000', 'ISO 22000'),
        ('iso14001', 'ISO 14001'),
        ('iso45001', 'ISO 45001'),
    ]
    title = models.CharField(max_length=300)
    doc_type = models.CharField(max_length=30, choices=DOC_TYPE_CHOICES)
    standard = models.CharField(max_length=20, choices=STANDARD_CHOICES)
    template_content = models.TextField()
    ai_prompt = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['standard', 'title']

    def __str__(self):
        return f"{self.title} ({self.standard})"


class GeneratedDocument(models.Model):
    STATUS_CHOICES = [
        ('draft', 'Qoralama'),
        ('sent', 'Yuborilgan'),
        ('approved', 'Tasdiqlangan'),
    ]
    expert = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='generated_docs')
    project = models.ForeignKey(Project, on_delete=models.CASCADE, null=True, blank=True, related_name='generated_docs')
    template = models.ForeignKey(DocumentTemplate, on_delete=models.SET_NULL, null=True, blank=True)
    title = models.CharField(max_length=300)
    content = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.title} — {self.expert.get_full_name()}"


class AuditChecklist(models.Model):
    expert = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='audit_checklists')
    project = models.ForeignKey(Project, on_delete=models.CASCADE, null=True, blank=True, related_name='audit_checklists')
    company_name = models.CharField(max_length=300)
    standard = models.CharField(max_length=20)
    audit_date = models.DateField()
    overall_score = models.IntegerField(default=0)
    is_completed = models.BooleanField(default=False)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-audit_date']

    def __str__(self):
        return f"{self.company_name} — {self.audit_date}"


class AuditChecklistItem(models.Model):
    STATUS_CHOICES = [
        ('compliant', 'Mos'),
        ('partial', 'Qisman'),
        ('non_compliant', 'Mos emas'),
        ('not_checked', 'Tekshirilmagan'),
    ]
    checklist = models.ForeignKey(AuditChecklist, on_delete=models.CASCADE, related_name='items')
    clause = models.CharField(max_length=20)
    question = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='not_checked')
    evidence = models.TextField(blank=True)
    finding = models.TextField(blank=True)
    order = models.IntegerField(default=0)

    class Meta:
        ordering = ['order']

    def __str__(self):
        return f"{self.checklist.company_name} — {self.clause}"


class ProjectTemplate(models.Model):
    STANDARD_CHOICES = [
        ('iso9001', 'ISO 9001'),
        ('iso22000', 'ISO 22000'),
        ('iso14001', 'ISO 14001'),
        ('iso45001', 'ISO 45001'),
    ]
    title = models.CharField(max_length=300)
    standard = models.CharField(max_length=20, choices=STANDARD_CHOICES)
    description = models.TextField()
    total_days = models.IntegerField(default=90)
    is_active = models.BooleanField(default=True)
    created_by = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, blank=True)

    class Meta:
        ordering = ['standard', 'title']

    def __str__(self):
        return f"{self.title} ({self.standard})"


class ProjectTemplateStep(models.Model):
    template = models.ForeignKey(ProjectTemplate, on_delete=models.CASCADE, related_name='steps')
    title = models.CharField(max_length=300)
    description = models.TextField()
    duration_days = models.IntegerField()
    order = models.IntegerField()
    deliverable = models.CharField(max_length=300, blank=True)

    class Meta:
        ordering = ['order']

    def __str__(self):
        return f"{self.template.title} — {self.order}. {self.title}"


class ClientCRM(models.Model):
    STATUS_CHOICES = [
        ('lead', "Potensial"),
        ('active', 'Faol'),
        ('completed', 'Yakunlangan'),
        ('paused', "To'xtatilgan"),
    ]
    expert = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='crm_clients')
    company_name = models.CharField(max_length=300)
    contact_person = models.CharField(max_length=200)
    phone = models.CharField(max_length=20, blank=True)
    email = models.EmailField(blank=True)
    industry = models.CharField(max_length=100, blank=True)
    target_standard = models.CharField(max_length=50, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='lead')
    project = models.ForeignKey(Project, on_delete=models.SET_NULL, null=True, blank=True, related_name='crm_entries')
    next_followup = models.DateField(null=True, blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-updated_at']

    def __str__(self):
        return f"{self.company_name} — {self.expert.get_full_name()}"


class CRMNote(models.Model):
    client = models.ForeignKey(ClientCRM, on_delete=models.CASCADE, related_name='crm_notes')
    author = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    note = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.client.company_name} — {self.created_at:%d.%m.%Y}"


class Proposal(models.Model):
    STATUS_CHOICES = [
        ('draft', 'Qoralama'),
        ('sent', 'Yuborilgan'),
        ('accepted', 'Qabul qilindi'),
        ('rejected', 'Rad etildi'),
    ]
    STANDARD_CHOICES = [
        ('ISO 9001', 'ISO 9001'),
        ('ISO 14001', 'ISO 14001'),
        ('ISO 45001', 'ISO 45001'),
        ('ISO 22000', 'ISO 22000'),
        ('ISO 27001', 'ISO 27001'),
        ('CE marking', 'CE marking'),
    ]
    expert = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='proposals')
    project = models.ForeignKey(Project, on_delete=models.SET_NULL, null=True, blank=True, related_name='proposals')
    company_name = models.CharField(max_length=300)
    contact_person = models.CharField(max_length=200, blank=True)
    standard = models.CharField(max_length=50)
    industry = models.CharField(max_length=100, blank=True)
    scope = models.TextField(blank=True, help_text='Loyiha qamrovi')
    price_min = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    price_max = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    duration_days = models.IntegerField(default=90)
    content = models.TextField(help_text='Taklifnoma matni (AI yoki qo\'lda)')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    valid_until = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.company_name} — {self.standard} [{self.status}]"

    @property
    def is_expired(self):
        from django.utils import timezone
        if not self.valid_until:
            return False
        return self.valid_until < timezone.now().date()

    @property
    def is_valid(self):
        return self.status in ('draft', 'sent') and not self.is_expired


class TimeLog(models.Model):
    expert = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='time_logs')
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='time_logs')
    date = models.DateField()
    hours = models.DecimalField(max_digits=4, decimal_places=1)
    description = models.CharField(max_length=300, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-date', '-created_at']

    def __str__(self):
        return f"{self.project} — {self.date} — {self.hours}h"
