from django.urls import path
from . import views

urlpatterns = [
    path('', views.post_list, name='blog_list'),
    path('<slug:slug>/like/', views.toggle_like, name='blog_toggle_like'),
    path('<slug:slug>/comment/', views.add_comment, name='blog_add_comment'),
    path('comment/<int:comment_pk>/delete/', views.delete_comment, name='blog_delete_comment'),
    path('<slug:slug>/', views.post_detail, name='blog_detail'),
]
