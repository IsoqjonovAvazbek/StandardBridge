from django.contrib.sitemaps import Sitemap
from django.urls import reverse
from .models import BlogPost


class BlogPostSitemap(Sitemap):
    changefreq = 'weekly'
    priority = 0.8

    def items(self):
        return BlogPost.objects.filter(is_published=True)

    def lastmod(self, obj):
        return obj.updated_at

    def location(self, obj):
        return f'/blog/{obj.slug}/'


class StaticSitemap(Sitemap):
    priority = 0.5
    changefreq = 'monthly'

    def items(self):
        return ['landing', 'blog_list', 'project_list']

    def location(self, item):
        return reverse(item)
