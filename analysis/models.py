from django.db import models
from accounts.models import CustomUser


class Industry(models.Model):
    ICON_CHOICES = [
        ('shirt', 'To\'qimachilik'),
        ('apple', 'Oziq-ovqat'),
        ('flask', 'Kimyo'),
        ('tool', 'Mashinasozlik'),
        ('home', 'Qurilish'),
        ('pill', 'Farmatsevtika'),
        ('leaf', 'Qishloq xo\'jaligi'),
        ('zap', 'Elektrotexnika'),
    ]

    name = models.CharField(max_length=200)
    name_ru = models.CharField(max_length=200, blank=True)
    name_en = models.CharField(max_length=200, blank=True)
    description = models.CharField(max_length=500, blank=True)
    description_ru = models.CharField(max_length=500, blank=True)
    description_en = models.CharField(max_length=500, blank=True)
    icon = models.CharField(max_length=50, default='box')
    is_active = models.BooleanField(default=True)
    order = models.IntegerField(default=0)

    class Meta:
        ordering = ['order']

    def __str__(self):
        return self.name

    def get_name(self, lang):
        if lang == 'ru' and self.name_ru:
            return self.name_ru
        if lang == 'en' and self.name_en:
            return self.name_en
        return self.name

    def get_description(self, lang):
        if lang == 'ru' and self.description_ru:
            return self.description_ru
        if lang == 'en' and self.description_en:
            return self.description_en
        return self.description


class Standard(models.Model):
    TYPE_CHOICES = [
        ('local', 'Mahalliy (UzDST/GOST)'),
        ('international', 'Xalqaro (ISO/CE/EN)'),
    ]

    code = models.CharField(max_length=100, unique=True)
    name = models.CharField(max_length=500)
    name_ru = models.CharField(max_length=500, blank=True)
    name_en = models.CharField(max_length=500, blank=True)
    type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    description = models.TextField(blank=True)
    description_ru = models.TextField(blank=True)
    description_en = models.TextField(blank=True)
    industry = models.ForeignKey(Industry, on_delete=models.SET_NULL, null=True, blank=True, related_name='standards')
    version = models.CharField(max_length=50, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.code} — {self.name}"

    def get_name(self, lang):
        if lang == 'ru' and self.name_ru:
            return self.name_ru
        if lang == 'en' and self.name_en:
            return self.name_en
        return self.name

    def get_description(self, lang):
        if lang == 'ru' and self.description_ru:
            return self.description_ru
        if lang == 'en' and self.description_en:
            return self.description_en
        return self.description


class StandardRoadmapStep(models.Model):
    """Standart uchun tayyor roadmap qadami — bazadan, AI tegmaydi."""
    standard = models.ForeignKey(Standard, on_delete=models.CASCADE, related_name='roadmap_template_steps')
    order = models.IntegerField(default=1)
    title = models.CharField(max_length=300)
    description = models.TextField()
    deliverables = models.JSONField(default=list)
    duration_days = models.IntegerField(default=14)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['standard', 'order']

    def __str__(self):
        return f"{self.standard.code} — {self.order}. {self.title}"


class GapAnalysis(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Kutilmoqda'),
        ('in_progress', 'Jarayonda'),
        ('completed', 'Bajarildi'),
        ('cancelled', 'Bekor qilindi'),
    ]

    entrepreneur = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='analyses')
    local_standard = models.ForeignKey(Standard, on_delete=models.SET_NULL, null=True, related_name='local_analyses')
    target_standard = models.ForeignKey(Standard, on_delete=models.SET_NULL, null=True, related_name='target_analyses')
    industry = models.ForeignKey(Industry, on_delete=models.SET_NULL, null=True, blank=True, related_name='analyses')
    company_info = models.TextField(blank=True)
    language = models.CharField(max_length=5, default='uz')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    ai_result = models.JSONField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.entrepreneur.company_name} — {self.target_standard}"


class GapItem(models.Model):
    PRIORITY_CHOICES = [
        ('critical', 'Kritik'),
        ('high', 'Yuqori'),
        ('medium', 'O\'rta'),
        ('low', 'Past'),
    ]

    analysis = models.ForeignKey(GapAnalysis, on_delete=models.CASCADE, related_name='gaps')
    title = models.CharField(max_length=300)
    description = models.TextField()
    clause = models.CharField(max_length=100, blank=True)
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default='medium')
    is_resolved = models.BooleanField(default=False)
    estimated_days = models.IntegerField(default=0)

    def __str__(self):
        return f"{self.title} ({self.get_priority_display()})"


class Roadmap(models.Model):
    analysis = models.OneToOneField(GapAnalysis, on_delete=models.CASCADE, related_name='roadmap')
    total_days = models.IntegerField(default=0)
    estimated_cost = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Yo'l xarita — {self.analysis}"


class RoadmapStep(models.Model):
    roadmap = models.ForeignKey(Roadmap, on_delete=models.CASCADE, related_name='steps')
    order = models.IntegerField(default=0)
    title = models.CharField(max_length=300)
    description = models.TextField()
    deliverables = models.JSONField(default=list, blank=True, help_text='Tayyorlanadigan hujjat/natijalar ro\'yxati')
    duration_days = models.IntegerField(default=0)
    is_completed = models.BooleanField(default=False)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['order']

    def clean_deliverables(self, value):
        if not isinstance(value, list):
            return []
        return [str(d)[:200] for d in value if str(d).strip()][:10]

    def save(self, *args, **kwargs):
        if self.deliverables is not None:
            self.deliverables = self.clean_deliverables(self.deliverables)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.order}. {self.title}"

class Question(models.Model):
    ANSWER_TYPE_CHOICES = [
        ('yes_no', 'Ha / Yo\'q'),
        ('yes_partial_no', 'Ha / Qisman / Yo\'q'),
        ('scale', 'Baho (1-5)'),
    ]

    standard = models.ForeignKey(Standard, on_delete=models.CASCADE, related_name='questions')
    text = models.CharField(max_length=500)
    text_ru = models.CharField(max_length=500, blank=True)
    text_en = models.CharField(max_length=500, blank=True)
    help_text = models.CharField(max_length=500, blank=True)
    help_text_ru = models.CharField(max_length=500, blank=True)
    help_text_en = models.CharField(max_length=500, blank=True)
    answer_type = models.CharField(max_length=20, choices=ANSWER_TYPE_CHOICES, default='yes_partial_no')
    order = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['order']

    def __str__(self):
        return f"{self.standard.code} — {self.text[:50]}"

    def get_text(self, lang):
        if lang == 'ru' and self.text_ru:
            return self.text_ru
        if lang == 'en' and self.text_en:
            return self.text_en
        return self.text

    def get_help(self, lang):
        if lang == 'ru' and self.help_text_ru:
            return self.help_text_ru
        if lang == 'en' and self.help_text_en:
            return self.help_text_en
        return self.help_text


class QuestionAnswer(models.Model):
    ANSWER_CHOICES = [
        ('yes', 'Ha'),
        ('partial', 'Qisman'),
        ('no', 'Yo\'q'),
    ]

    analysis = models.ForeignKey(GapAnalysis, on_delete=models.CASCADE, related_name='answers')
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    answer = models.CharField(max_length=20, choices=ANSWER_CHOICES)
    note = models.TextField(blank=True)

    def __str__(self):
        return f"{self.question.text[:30]} — {self.answer}"


class DisclaimerAcceptance(models.Model):
    """Tracks when a user accepted the AI analysis legal disclaimer."""
    CURRENT_VERSION = '1.0'

    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='disclaimer_acceptances')
    accepted_at = models.DateTimeField(auto_now_add=True)
    ip_address = models.CharField(max_length=45, blank=True)   # up to IPv6 length
    version = models.CharField(max_length=20, default='1.0')

    class Meta:
        ordering = ['-accepted_at']
        # One acceptance record per user per disclaimer version
        unique_together = [('user', 'version')]

    def __str__(self):
        return f"{self.user.username} — v{self.version} — {self.accepted_at:%d.%m.%Y %H:%M}"