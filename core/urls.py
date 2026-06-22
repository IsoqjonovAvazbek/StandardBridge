from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.db import models
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
    f = open(sw_path, 'rb')
    response = FileResponse(f, content_type='application/javascript')
    response['Service-Worker-Allowed'] = '/'
    return response


@login_required
def protected_media(request, path):
    """Authenticated foydalanuvchilarga media fayl berish. Path traversal himoyasi bor."""
    base = os.path.realpath(settings.MEDIA_ROOT)
    full = os.path.realpath(os.path.join(base, path))
    # Path traversal: fayl MEDIA_ROOT ichida bo'lishi shart
    if not full.startswith(base + os.sep) and full != base:
        raise Http404
    if not os.path.isfile(full):
        raise Http404
    # Avatar va public resurslar — barcha login qilganlarga ochiq
    # Loyiha hujjatlari — faqat tegishli entrepreneur/expert ko'ra oladi
    norm = path.replace('\\', '/')
    if norm.startswith('documents/') or norm.startswith('qms/') or norm.startswith('chat/'):
        _check_document_access(request, norm)
    return FileResponse(open(full, 'rb'))


def _check_document_access(request, norm_path):
    """Hujjat egasi yoki unga ulangan mutaxassis/tadbirkor emasni tekshir."""
    from experts.models import Document, Project
    from qms.models import QMSDocument
    user = request.user
    # Agar admin bo'lsa — to'liq ruxsat
    if user.is_staff or user.is_admin():
        return
    # Loyiha hujjatlari (documents/)
    if norm_path.startswith('documents/'):
        allowed = Document.objects.filter(file=norm_path).filter(
            models.Q(project__entrepreneur=user) | models.Q(project__expert=user)
        ).exists()
        if not allowed:
            raise Http404
    # QMS hujjatlari
    elif norm_path.startswith('qms/'):
        allowed = QMSDocument.objects.filter(file=norm_path, company=user).exists()
        if not allowed:
            raise Http404


urlpatterns = [
    path('admin/', admin.site.urls),
    path('health/', health_check, name='health_check'),
    path('sw.js', service_worker_view, name='service_worker'),
    path('offline/', TemplateView.as_view(template_name='pwa/offline.html'), name='pwa_offline'),
    path('sitemap.xml', sitemap, {'sitemaps': _sitemaps}, name='django.contrib.sitemaps.views.sitemap'),
    path('robots.txt', TemplateView.as_view(template_name='robots.txt', content_type='text/plain')),
    path('', include('accounts.urls')),
    path('accounts/', include('allauth.urls')),
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