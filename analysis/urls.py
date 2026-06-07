from django.urls import path
from . import views

urlpatterns = [
    path('', views.entrepreneur_dashboard, name='entrepreneur_dashboard'),
    path('new/', views.select_industry, name='select_industry'),
    path('new/<int:industry_id>/', views.select_standards, name='select_standards'),
    path('new/<int:industry_id>/questions/', views.answer_questions, name='answer_questions'),
    path('new/<int:industry_id>/analyze/', views.run_analysis, name='run_analysis'),
    path('<int:pk>/processing/', views.analysis_processing, name='analysis_processing'),
    path('<int:pk>/processing/retry/', views.analysis_retry, name='analysis_retry'),
    path('<int:pk>/retake/', views.analysis_retake, name='analysis_retake'),
    path('<int:pk>/status/', views.analysis_status, name='analysis_status'),
    path('<int:pk>/', views.analysis_detail, name='analysis_detail'),
    path('<int:pk>/print/', views.analysis_print, name='analysis_print'),
    path('<int:pk>/to-qms/', views.gaps_to_qms, name='gaps_to_qms'),
    path('<int:pk>/gap/<int:gap_pk>/toggle/', views.gap_toggle_resolved, name='gap_toggle_resolved'),
    path('<int:pk>/roadmap/', views.roadmap_view, name='roadmap'),
    path('<int:pk>/roadmap/step/<int:step_pk>/toggle/', views.roadmap_step_toggle, name='roadmap_step_toggle'),
    path('<int:pk>/delete/', views.analysis_delete, name='analysis_delete'),
    path('projects/', views.entrepreneur_projects, name='entrepreneur_projects'),
    path('wallet/', views.entrepreneur_wallet, name='entrepreneur_wallet'),
    path('disclaimer/accept/', views.accept_disclaimer, name='accept_disclaimer'),
]