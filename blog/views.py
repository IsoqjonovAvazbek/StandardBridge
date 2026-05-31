from django.shortcuts import render, get_object_or_404
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
    post.views_count += 1
    post.save(update_fields=['views_count'])

    related = BlogPost.objects.filter(
        is_published=True, category=post.category
    ).exclude(pk=post.pk)[:3]

    return render(request, 'blog/post_detail.html', {
        'post': post,
        'related': related,
    })
