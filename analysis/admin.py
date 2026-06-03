from django.contrib import admin
from .models import Standard, GapAnalysis, GapItem, Roadmap, RoadmapStep, Industry, Question, QuestionAnswer, StandardRoadmapStep


@admin.register(Industry)
class IndustryAdmin(admin.ModelAdmin):
    list_display = ['name', 'icon', 'order', 'is_active']
    list_editable = ['order', 'is_active']


class QuestionInline(admin.TabularInline):
    model = Question
    extra = 3
    fields = ['text', 'help_text', 'answer_type', 'order', 'is_active']


@admin.register(Standard)
class StandardAdmin(admin.ModelAdmin):
    list_display = ['code', 'name', 'type', 'industry', 'is_active']
    list_filter = ['type', 'industry', 'is_active']
    search_fields = ['code', 'name']
    inlines = [QuestionInline]


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ['standard', 'text', 'answer_type', 'order', 'is_active']
    list_filter = ['standard', 'is_active']
    search_fields = ['text']


@admin.register(GapAnalysis)
class GapAnalysisAdmin(admin.ModelAdmin):
    list_display = ['entrepreneur', 'local_standard', 'target_standard', 'status', 'created_at']
    list_filter = ['status']
    search_fields = ['entrepreneur__company_name']


@admin.register(GapItem)
class GapItemAdmin(admin.ModelAdmin):
    list_display = ['title', 'analysis', 'priority', 'is_resolved', 'estimated_days']
    list_filter = ['priority', 'is_resolved']


@admin.register(Roadmap)
class RoadmapAdmin(admin.ModelAdmin):
    list_display = ['analysis', 'total_days', 'estimated_cost', 'created_at']


@admin.register(RoadmapStep)
class RoadmapStepAdmin(admin.ModelAdmin):
    list_display = ['title', 'roadmap', 'order', 'duration_days', 'is_completed']
    list_filter = ['is_completed']


@admin.register(StandardRoadmapStep)
class StandardRoadmapStepAdmin(admin.ModelAdmin):
    list_display = ['standard', 'order', 'title', 'duration_days', 'is_active']
    list_filter = ['standard', 'is_active']
    list_editable = ['order', 'duration_days', 'is_active']
    search_fields = ['title', 'description']
    ordering = ['standard', 'order']