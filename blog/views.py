from django.shortcuts import render, get_object_or_404
from django.db.models import F
from .models import BlogPost, Category


def post_list(request):
    posts = BlogPost.objects.filter(is_published=True)
    categories = Category.objects.all()
    category_slug = request.GET.get('category', '')

    if category_slug:
        posts = posts.filter(category__slug=category_slug)

    return render(request, 'blog/post_list.html', {
        'posts': posts,
        'categories': categories,
        'selected_category': category_slug,
    })


def post_detail(request, slug):
    post = get_object_or_404(BlogPost, slug=slug, is_published=True)
    BlogPost.objects.filter(pk=post.pk).update(views_count=F('views_count') + 1)
    post.refresh_from_db(fields=['views_count'])

    related = BlogPost.objects.filter(
        is_published=True, category=post.category
    ).exclude(pk=post.pk)[:3]

    return render(request, 'blog/post_detail.html', {
        'post': post,
        'related': related,
    })
