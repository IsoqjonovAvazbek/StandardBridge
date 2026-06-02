from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.http import JsonResponse

def health_check(request):
    return JsonResponse({'status': 'ok'})

urlpatterns = [
    path('admin/', admin.site.urls),
    path('health/', health_check, name='health_check'),
    path('', include('accounts.urls')),
    path('analysis/', include('analysis.urls')),
    path('experts/', include('experts.urls')),
    path('blog/', include('blog.urls')),
    path('qms/', include('qms.urls')),
    path('expert-tools/', include('expert_tools.urls')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)