from django.contrib import admin
from .models import (
    ChecklistItem, ChecklistResponse, QMSDocument, QMSDocumentVersion,
    NonConformity, AuditSchedule, RiskItem, TrainingRecord
)


@admin.register(ChecklistItem)
class ChecklistItemAdmin(admin.ModelAdmin):
    list_display = ['standard', 'clause', 'question', 'order', 'is_active']
    list_editable = ['order', 'is_active']
    list_filter = ['standard', 'is_active']
    search_fields = ['question', 'clause']


@admin.register(RiskItem)
class RiskItemAdmin(admin.ModelAdmin):
    list_display = ['company', 'standard', 'process_area', 'likelihood', 'impact', 'risk_score', 'status', 'created_at']
    list_filter = ['standard', 'status']
    search_fields = ['process_area', 'description', 'company__company_name']
    readonly_fields = ['created_at']

    def risk_score(self, obj):
        return obj.risk_score
    risk_score.short_description = 'Ball'


@admin.register(TrainingRecord)
class TrainingRecordAdmin(admin.ModelAdmin):
    list_display = ['company', 'employee_name', 'training_name', 'date_completed', 'expiry_date', 'is_expired']
    list_filter = ['date_completed']
    search_fields = ['employee_name', 'training_name', 'company__company_name']
    readonly_fields = ['created_at']

    def is_expired(self, obj):
        return obj.is_expired
    is_expired.boolean = True
    is_expired.short_description = 'Muddati o\'tgan?'


@admin.register(NonConformity)
class NonConformityAdmin(admin.ModelAdmin):
    list_display = ['code', 'company', 'title', 'severity', 'status', 'is_effective_verified', 'created_at']
    list_filter = ['severity', 'status', 'is_effective_verified']
    search_fields = ['title', 'company__company_name', 'code']


@admin.register(AuditSchedule)
class AuditScheduleAdmin(admin.ModelAdmin):
    list_display = ['company', 'audit_type', 'standard', 'planned_date', 'status']
    list_filter = ['audit_type', 'status']
