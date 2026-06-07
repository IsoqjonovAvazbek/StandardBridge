from django.db import models
from accounts.models import CustomUser


class Category(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True)
    icon = models.CharField(max_length=10, blank=True, help_text='Emoji icon')

    def __str__(self):
        return self.name

    class Meta:
        verbose_name_plural = 'Categories'


class BlogPost(models.Model):
    title = models.CharField(max_length=300)
    slug = models.SlugField(unique=True, max_length=300)
    excerpt = models.TextField(max_length=500, blank=True, help_text='Qisqacha tavsif (card uchun)')
    content = models.TextField()
    author = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, blank=True)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True, related_name='posts')
    cover_image = models.URLField(blank=True, help_text='Rasm URL manzili')
    LANG_CHOICES = [('uz', 'O\'zbek'), ('ru', 'Русский'), ('en', 'English')]
    language = models.CharField(max_length=5, choices=LANG_CHOICES, default='uz')
    group_key = models.SlugField(max_length=200, blank=True, db_index=True,
                                 help_text='Bir xil maqolaning turli tillari uchun umumiy kalit')
    is_published = models.BooleanField(default=False)
    is_featured = models.BooleanField(default=False, help_text='Asosiy featured post sifatida ko\'rsatish')
    views_count = models.PositiveIntegerField(default=0)
    read_time = models.PositiveIntegerField(default=5, help_text="O'qish vaqti (daqiqa)")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['is_published', 'language'], name='blog_post_pub_lang_idx'),
            models.Index(fields=['is_featured'], name='blog_post_featured_idx'),
        ]

    def __str__(self):
        return self.title

    def likes_count(self):
        return self.likes.count()

    def comments_count(self):
        return self.comments.filter(is_approved=True).count()


class BlogComment(models.Model):
    post = models.ForeignKey(BlogPost, on_delete=models.CASCADE, related_name='comments')
    author = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    content = models.TextField(max_length=1000)
    created_at = models.DateTimeField(auto_now_add=True)
    is_approved = models.BooleanField(default=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f'{self.author.username} → {self.post.title[:40]}'


class BlogLike(models.Model):
    post = models.ForeignKey(BlogPost, on_delete=models.CASCADE, related_name='likes')
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['post', 'user']

    def __str__(self):
        return f'{self.user.username} likes {self.post.title[:40]}'
