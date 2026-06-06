from django.contrib import admin
from django import forms
from .models import BlogPost, Category, BlogComment, BlogLike


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'icon']
    prepopulated_fields = {'slug': ('name',)}


class BlogPostAdminForm(forms.ModelForm):
    class Meta:
        model = BlogPost
        fields = '__all__'
        widgets = {
            'content': forms.Textarea(attrs={
                'class': 'markdown-editor',
                'rows': 30,
                'style': 'font-family: monospace; font-size: 13px;',
            }),
            'excerpt': forms.Textarea(attrs={'rows': 3}),
        }


@admin.register(BlogPost)
class BlogPostAdmin(admin.ModelAdmin):
    form = BlogPostAdminForm
    list_display = ['title', 'language', 'category', 'author', 'is_published', 'is_featured', 'views_count', 'created_at']
    list_filter = ['is_published', 'is_featured', 'category', 'language']
    list_editable = ['is_published', 'is_featured']
    prepopulated_fields = {'slug': ('title',)}
    search_fields = ['title', 'content', 'excerpt']
    readonly_fields = ['views_count', 'created_at', 'updated_at']
    fieldsets = (
        ('Asosiy', {'fields': ('title', 'slug', 'language', 'group_key', 'category', 'author', 'is_published', 'is_featured')}),
        ('Kontent', {'fields': ('excerpt', 'content', 'cover_image', 'read_time')}),
        ('Statistika', {'fields': ('views_count', 'created_at', 'updated_at')}),
    )

    class Media:
        css = {'all': ['https://unpkg.com/easymde/dist/easymde.min.css']}
        js = ['https://unpkg.com/easymde/dist/easymde.min.js', '/static/js/blog_admin_editor.js']


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
