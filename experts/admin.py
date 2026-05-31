from django.contrib import admin
from .models import Project, ProjectUpdate, Document, Review, Notification


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ['id', 'entrepreneur', 'expert', 'status', 'expert_price', 'created_at']
    list_filter = ['status']
    search_fields = ['entrepreneur__company_name', 'expert__first_name']


@admin.register(ProjectUpdate)
class ProjectUpdateAdmin(admin.ModelAdmin):
    list_display = ['project', 'author', 'created_at']
    search_fields = ['message']


@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = ['title', 'project', 'uploaded_by', 'doc_type', 'created_at']
    list_filter = ['doc_type']
    search_fields = ['title']


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ['project', 'entrepreneur', 'expert', 'rating', 'created_at']
    list_filter = ['rating']


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ['user', 'title', 'is_read', 'created_at']
    list_filter = ['is_read']
    search_fields = ['title', 'message']