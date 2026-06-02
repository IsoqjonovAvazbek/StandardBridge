from django.urls import path
from django.contrib.auth import views as auth_views
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
    # Parol tiklash (Django built-in)
    path('accounts/password-reset/', auth_views.PasswordResetView.as_view(
        template_name='accounts/password_reset.html',
        email_template_name='accounts/password_reset_email.html',
        subject_template_name='accounts/password_reset_subject.txt',
        success_url='/accounts/password-reset/done/',
    ), name='password_reset'),
    path('accounts/password-reset/done/', auth_views.PasswordResetDoneView.as_view(
        template_name='accounts/password_reset_done.html',
    ), name='password_reset_done'),
    path('accounts/password-reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(
        template_name='accounts/password_reset_confirm.html',
        success_url='/accounts/password-reset/complete/',
    ), name='password_reset_confirm'),
    path('accounts/password-reset/complete/', auth_views.PasswordResetCompleteView.as_view(
        template_name='accounts/password_reset_complete.html',
    ), name='password_reset_complete'),
]