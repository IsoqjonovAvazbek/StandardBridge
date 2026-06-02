from django.shortcuts import render, get_object_or_404
from django.db.models import F
from django.core.paginator import Paginator
from .models import BlogPost, Category


def post_list(request):
    posts = BlogPost.objects.filter(is_published=True).order_by('-created_at')
    categories = Category.objects.all()
    category_slug = request.GET.get('category', '')
    search_q = request.GET.get('q', '').strip()

    if category_slug:
        posts = posts.filter(category__slug=category_slug)
    if search_q:
        posts = posts.filter(title__icontains=search_q)

    paginator = Paginator(posts, 9)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)

    return render(request, 'blog/post_list.html', {
        'posts': page_obj,
        'page_obj': page_obj,
        'categories': categories,
        'selected_category': category_slug,
        'search_q': search_q,
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
