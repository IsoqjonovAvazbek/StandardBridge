from django.contrib import admin
from .models import BlogPost, Category, BlogComment, BlogLike


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'icon']
    prepopulated_fields = {'slug': ('name',)}


@admin.register(BlogPost)
class BlogPostAdmin(admin.ModelAdmin):
    list_display = ['title', 'category', 'author', 'is_published', 'is_featured', 'views_count', 'created_at']
    list_filter = ['is_published', 'is_featured', 'category']
    list_editable = ['is_published', 'is_featured']
    prepopulated_fields = {'slug': ('title',)}
    search_fields = ['title', 'content', 'excerpt']
    readonly_fields = ['views_count', 'created_at', 'updated_at']
    fieldsets = (
        ('Asosiy', {'fields': ('title', 'slug', 'category', 'author', 'is_published', 'is_featured')}),
        ('Kontent', {'fields': ('excerpt', 'content', 'cover_image', 'read_time')}),
        ('Statistika', {'fields': ('views_count', 'created_at', 'updated_at')}),
    )


@admin.register(BlogComment)
class BlogCommentAdmin(admin.ModelAdmin):
    list_display = ['author', 'post', 'is_approved', 'created_at']
    list_filter = ['is_approved']
    list_editable = ['is_approved']
    search_fields = ['author__username', 'content']
    readonly_fields = ['created_at']


@admin.register(BlogLike)
class BlogLikeAdmin(admin.ModelAdmin):
    list_display = ['user', 'post', 'created_at']
    readonly_fields = ['created_at']
