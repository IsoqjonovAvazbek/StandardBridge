from django.contrib import admin
from .models import BlogPost, Category


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug']
    prepopulated_fields = {'slug': ('name',)}


@admin.register(BlogPost)
class BlogPostAdmin(admin.ModelAdmin):
    list_display = ['title', 'category', 'author', 'is_published', 'views_count', 'created_at']
    list_filter = ['is_published', 'category']
    list_editable = ['is_published']
    prepopulated_fields = {'slug': ('title',)}
    search_fields = ['title', 'content']
    readonly_fields = ['views_count', 'created_at', 'updated_at']
    fieldsets = (
        ('Asosiy', {'fields': ('title', 'slug', 'category', 'author', 'is_published')}),
        ('Kontent', {'fields': ('excerpt', 'content', 'cover_image', 'read_time')}),
        ('Statistika', {'fields': ('views_count', 'created_at', 'updated_at')}),
    )
