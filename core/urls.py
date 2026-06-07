from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.http import JsonResponse, FileResponse, Http404
from django.contrib.auth.decorators import login_required
from django.views.decorators.cache import cache_control
from django.contrib.sitemaps.views import sitemap
from django.views.generic import TemplateView
from blog.sitemaps import BlogPostSitemap, StaticSitemap
import os

_sitemaps = {
    'blog': BlogPostSitemap,
    'static': StaticSitemap,
}


def health_check(request):
    return JsonResponse({'status': 'ok'})


@cache_control(no_cache=True, must_revalidate=True)
def service_worker_view(request):
    sw_path = os.path.join(settings.BASE_DIR, 'static', 'sw.js')
    if not os.path.isfile(sw_path):
        raise Http404
    response = FileResponse(open(sw_path, 'rb'), content_type='application/javascript')
    response['Service-Worker-Allowed'] = '/'
    return response


@login_required
def protected_media(request, path):
    """Media fayllarni faqat login qilgan foydalanuvchilarga berish."""
    base = os.path.realpath(settings.MEDIA_ROOT)
    full = os.path.realpath(os.path.join(base, path))
    # Path traversal himoyasi: MEDIA_ROOT ichida ekanini tekshir
    if not full.startswith(base + os.sep) and full != base:
        raise Http404
    if not os.path.isfile(full):
        raise Http404
    return FileResponse(open(full, 'rb'))


urlpatterns = [
    path('admin/', admin.site.urls),
    path('health/', health_check, name='health_check'),
    path('sw.js', service_worker_view, name='service_worker'),
    path('offline/', TemplateView.as_view(template_name='pwa/offline.html'), name='pwa_offline'),
    path('sitemap.xml', sitemap, {'sitemaps': _sitemaps}, name='django.contrib.sitemaps.views.sitemap'),
    path('robots.txt', TemplateView.as_view(template_name='robots.txt', content_type='text/plain')),
    path('', include('accounts.urls')),
    path('analysis/', include('analysis.urls')),
    path('experts/', include('experts.urls')),
    path('blog/', include('blog.urls')),
    path('qms/', include('qms.urls')),
    path('expert-tools/', include('expert_tools.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
else:
    urlpatterns += [path('media/<path:path>', protected_media, name='protected_media')]