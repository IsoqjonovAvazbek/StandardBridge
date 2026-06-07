from django.shortcuts import render, get_object_or_404
from django.db.models import F, Count
from django.core.paginator import Paginator
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from .models import BlogPost, Category, BlogComment, BlogLike


def post_list(request):
    from django.core.cache import cache
    lang = request.session.get('lang', 'uz')
    qs = BlogPost.objects.filter(is_published=True, language=lang).select_related('category', 'author')
    _cat_key = f'blog_categories_{lang}'
    categories = cache.get(_cat_key)
    if categories is None:
        categories = list(
            Category.objects
            .filter(posts__is_published=True, posts__language=lang)
            .annotate(post_count=Count('posts'))
            .distinct()
        )
        cache.set(_cat_key, categories, 300)
    category_slug = request.GET.get('category', '').strip()
    search_q = request.GET.get('q', '').strip()

    if category_slug:
        qs = qs.filter(category__slug=category_slug)
    if search_q:
        qs = qs.filter(title__icontains=search_q) | qs.filter(excerpt__icontains=search_q)

    total_count = qs.count()

    # Featured hero post (only on main page, no search/filter)
    featured = None
    page_number = request.GET.get('page', '1')
    if not category_slug and not search_q and page_number == '1':
        featured = qs.filter(is_featured=True).first() or qs.first()

    paginator = Paginator(qs, 9)
    page_obj = paginator.get_page(page_number)

    return render(request, 'blog/post_list.html', {
        'posts': page_obj,
        'page_obj': page_obj,
        'categories': categories,
        'selected_category': category_slug,
        'search_q': search_q,
        'total_count': total_count,
        'featured': featured,
    })


def post_detail(request, slug):
    post = get_object_or_404(BlogPost, slug=slug, is_published=True)
    viewed_key = f'viewed_post_{post.pk}'
    if not request.session.get(viewed_key):
        BlogPost.objects.filter(pk=post.pk).update(views_count=F('views_count') + 1)
        post.refresh_from_db(fields=['views_count'])
        request.session[viewed_key] = True

    lang = post.language
    related = list(
        BlogPost.objects
        .filter(is_published=True, language=lang, category=post.category)
        .exclude(pk=post.pk)
        .select_related('category', 'author')[:3]
    )
    if not related:
        related = list(
            BlogPost.objects
            .filter(is_published=True, language=lang)
            .exclude(pk=post.pk)
            .select_related('category', 'author')[:3]
        )

    comments = post.comments.filter(is_approved=True).select_related('author')
    likes_count = post.likes.count()
    user_liked = request.user.is_authenticated and post.likes.filter(user=request.user).exists()

    return render(request, 'blog/post_detail.html', {
        'post': post,
        'related': related,
        'comments': comments,
        'likes_count': likes_count,
        'user_liked': user_liked,
    })


@login_required
@require_POST
def toggle_like(request, slug):
    post = get_object_or_404(BlogPost, slug=slug, is_published=True)
    like, created = BlogLike.objects.get_or_create(post=post, user=request.user)
    if not created:
        like.delete()
        liked = False
    else:
        liked = True
    return JsonResponse({'liked': liked, 'count': post.likes.count()})


@login_required
@require_POST
def add_comment(request, slug):
    post = get_object_or_404(BlogPost, slug=slug, is_published=True)
    content = request.POST.get('content', '').strip()
    if not content:
        return JsonResponse({'error': 'empty'}, status=400)
    comment = BlogComment.objects.create(post=post, author=request.user, content=content[:1000])
    return JsonResponse({
        'id': comment.pk,
        'author': request.user.get_full_name() or request.user.username,
        'initial': (request.user.first_name or request.user.username)[0].upper(),
        'content': comment.content,
        'created_at': comment.created_at.strftime('%d.%m.%Y %H:%M'),
    })


@login_required
@require_POST
def delete_comment(request, comment_pk):
    comment = get_object_or_404(BlogComment, pk=comment_pk)
    if comment.author_id != request.user.pk and not request.user.is_staff:
        return JsonResponse({'error': 'forbidden'}, status=403)
    comment.delete()
    return JsonResponse({'deleted': True})
