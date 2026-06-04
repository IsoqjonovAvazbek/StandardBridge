from django.urls import path
from . import views

urlpatterns = [
    path('', views.qms_dashboard, name='qms_dashboard'),
    path('checklist/', views.qms_checklist, name='qms_checklist'),
    path('checklist/update/', views.update_checklist, name='update_checklist'),
    path('documents/', views.qms_documents, name='qms_documents'),
    path('documents/upload/', views.upload_document, name='upload_document'),
    path('documents/<int:pk>/delete/', views.delete_document, name='delete_document'),
    path('documents/<int:pk>/update-version/', views.update_document_version, name='update_document_version'),
    path('nonconformities/', views.nonconformities, name='nonconformities'),
    path('nonconformities/add/', views.add_nonconformity, name='add_nonconformity'),
    path('nonconformities/<int:pk>/update/', views.update_nonconformity, name='update_nonconformity'),
    path('audit/', views.audit_schedule, name='audit_schedule'),
    path('audit/add/', views.add_audit, name='add_audit'),
    path('audit/<int:pk>/update/', views.update_audit, name='update_audit'),
    path('checklist/print/', views.checklist_print, name='checklist_print'),
    # AI yordamchi
    path('nonconformities/<int:pk>/ai-suggest/', views.ai_nc_suggestion, name='ai_nc_suggestion'),
    path('documents/ai-generate/', views.qms_generate_policy, name='qms_generate_policy'),
    # Document viewer (AI .md hujjatlar uchun)
    path('documents/<int:pk>/view/', views.qms_document_view, name='qms_document_view'),
    # Eksport
    path('checklist/export/', views.export_checklist_csv, name='export_checklist_csv'),
    path('nonconformities/export/', views.export_nc_csv, name='export_nc_csv'),
    # Risk Register
    path('risks/', views.risk_register, name='risk_register'),
    path('risks/add/', views.add_risk, name='add_risk'),
    path('risks/<int:pk>/update/', views.update_risk, name='update_risk'),
    path('risks/<int:pk>/delete/', views.delete_risk, name='delete_risk'),
    path('risks/export/', views.export_risk_csv, name='export_risk_csv'),
    # Training Records
    path('training/', views.training_records, name='training_records'),
    path('training/add/', views.add_training, name='add_training'),
    path('training/<int:pk>/delete/', views.delete_training, name='delete_training'),
    path('training/export/', views.export_training_csv, name='export_training_csv'),
    # NC Effectiveness
    path('nonconformities/<int:pk>/verify/', views.verify_nc_effectiveness, name='verify_nc_effectiveness'),
]
