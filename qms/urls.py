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
    # Eksport
    path('checklist/export/', views.export_checklist_csv, name='export_checklist_csv'),
    path('nonconformities/export/', views.export_nc_csv, name='export_nc_csv'),
]
