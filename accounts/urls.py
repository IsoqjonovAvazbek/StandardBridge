from django.urls import path
from . import views

urlpatterns = [
    path('', views.landing, name='landing'),
    path('register/', views.register_view, name='register'),
    path('accounts/login/', views.login_view, name='login'),
    path('accounts/logout/', views.logout_view, name='logout'),
    path('role-select/', views.role_select, name='role_select'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('admin-panel/', views.admin_panel, name='admin_panel'),
    path('admin-panel/verify/<int:pk>/', views.verify_expert_action, name='verify_expert_action'),
    path('admin-panel/withdrawal/<int:pk>/process/', views.admin_process_withdrawal, name='admin_process_withdrawal'),
    path('admin-panel/dispute/<int:pk>/resolve/', views.admin_resolve_dispute, name='admin_resolve_dispute'),
    path('profile/', views.entrepreneur_profile_view, name='entrepreneur_profile'),
    path('referral/', views.referral_view, name='referral'),
    path('set-language/', views.set_language_view, name='set_language'),
]