from django.urls import path
from . import views

urlpatterns = [
    # Dashboard
    path('', views.expert_tools_dashboard, name='expert_tools_dashboard'),

    # Document generator
    path('documents/', views.document_list, name='expert_doc_list'),
    path('documents/generate/', views.generate_document, name='generate_document'),
    path('documents/<int:pk>/', views.document_detail, name='expert_doc_detail'),
    path('documents/<int:pk>/edit/', views.edit_document, name='edit_document'),
    path('documents/<int:pk>/delete/', views.delete_document, name='delete_expert_doc'),

    # Audit checklist
    path('audit/', views.audit_list, name='audit_list'),
    path('audit/new/', views.new_audit, name='new_audit'),
    path('audit/<int:pk>/', views.audit_detail, name='audit_detail'),
    path('audit/<int:pk>/update-item/', views.update_audit_item, name='update_audit_item'),
    path('audit/<int:pk>/complete/', views.complete_audit, name='complete_audit'),
    path('audit/<int:pk>/mobile/', views.audit_mobile, name='audit_mobile'),
    path('audit/from-analysis/<int:project_id>/', views.audit_from_analysis, name='audit_from_analysis'),

    # Project templates
    path('templates/', views.project_templates, name='project_templates'),
    path('templates/<int:pk>/apply/<int:project_pk>/', views.apply_template, name='apply_template'),

    # CRM
    path('crm/', views.crm_list, name='crm_list'),
    path('crm/add/', views.crm_add, name='crm_add'),
    path('crm/<int:pk>/', views.crm_detail, name='crm_detail'),
    path('crm/<int:pk>/update/', views.crm_update, name='crm_update'),
    path('crm/<int:pk>/delete/', views.crm_delete, name='crm_delete'),
    path('crm/<int:pk>/note/', views.crm_add_note, name='crm_add_note'),
    # Proposal Generator
    path('proposals/', views.proposal_list, name='proposal_list'),
    path('proposals/create/', views.create_proposal, name='create_proposal'),
    path('proposals/<int:pk>/', views.proposal_detail, name='proposal_detail'),
    path('proposals/<int:pk>/edit/', views.edit_proposal, name='edit_proposal'),
    path('proposals/<int:pk>/delete/', views.delete_proposal, name='delete_proposal'),
    path('proposals/<int:pk>/print/', views.proposal_print, name='proposal_print'),
    # Time Tracker
    path('time/', views.time_logs, name='time_logs'),
    path('time/add/', views.add_time_log, name='add_time_log'),
    path('time/<int:pk>/delete/', views.delete_time_log, name='delete_time_log'),
    # Earnings Dashboard
    path('earnings/', views.earnings_dashboard, name='earnings_dashboard'),
    # Audit Print
    path('audit/<int:pk>/print/', views.audit_print, name='audit_print'),
]
