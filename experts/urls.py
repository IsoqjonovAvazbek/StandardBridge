from django.urls import path
from . import views

urlpatterns = [
    path('dashboard/', views.expert_dashboard, name='expert_dashboard'),
    path('projects/', views.project_list, name='project_list'),
    path('projects/<int:pk>/', views.project_detail, name='project_detail'),
    path('projects/<int:pk>/update/', views.project_update, name='project_update'),
    path('projects/<int:pk>/messages/', views.project_messages, name='project_messages'),
    path('projects/<int:pk>/price/', views.project_set_price, name='project_set_price'),
    path('projects/<int:pk>/accept/', views.project_accept, name='project_accept'),
    path('projects/<int:pk>/decline/', views.project_decline, name='project_decline'),
    path('projects/<int:pk>/cancel/', views.project_cancel, name='project_cancel'),
    path('projects/<int:pk>/complete/', views.project_complete, name='project_complete'),
    path('projects/<int:pk>/request-revision/', views.project_request_revision, name='project_request_revision'),
    path('projects/<int:pk>/step/<int:step_pk>/toggle/', views.project_step_toggle, name='project_step_toggle'),
    path('projects/<int:pk>/review/', views.leave_review, name='leave_review'),
    path('notifications/', views.notifications, name='notifications'),
    path('profile/', views.expert_profile, name='expert_profile'),
    path('profile/edit/', views.expert_profile_edit, name='expert_profile_edit'),
    path('wallet/', views.wallet, name='wallet'),
    path('payment/<int:project_pk>/', views.payment_page, name='payment_page'),
    path('payment/<int:project_pk>/confirm/', views.payment_confirm, name='payment_confirm'),
    path('payment/<int:project_pk>/release/', views.payment_release, name='payment_release'),
    path('send/<int:expert_pk>/<int:analysis_pk>/', views.send_to_expert, name='send_to_expert'),
    path('expert/<int:expert_pk>/', views.expert_detail, name='expert_detail'),
    # Click webhook endpoints
    path('click/prepare/', views.click_prepare, name='click_prepare'),
    path('click/complete/', views.click_complete, name='click_complete'),
    # Counter-offer
    path('projects/<int:pk>/counter/', views.project_counter_offer, name='project_counter_offer'),
    path('projects/<int:pk>/counter/respond/', views.project_respond_counter, name='project_respond_counter'),
    # Dispute
    path('projects/<int:pk>/dispute/', views.open_dispute, name='open_dispute'),
    # Roadmap step management (expert)
    path('projects/<int:pk>/add-step/', views.add_roadmap_step, name='add_roadmap_step'),
    path('projects/<int:pk>/step/<int:step_pk>/delete/', views.delete_roadmap_step, name='delete_roadmap_step'),
    path('projects/<int:pk>/step/<int:step_pk>/edit/', views.edit_roadmap_step, name='edit_roadmap_step'),
    path('projects/<int:pk>/contract/', views.project_contract, name='project_contract'),
    # Qo'shimcha ish so'rovi (scope request)
    path('projects/<int:pk>/scope-request/', views.scope_request_send, name='scope_request_send'),
    path('projects/<int:pk>/scope-request/<int:sr_pk>/respond/', views.scope_request_respond, name='scope_request_respond'),
]