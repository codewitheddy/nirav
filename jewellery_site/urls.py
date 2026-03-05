from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import RedirectView
from django.http import JsonResponse
from django.db import connection

def health_check(request):
    """Health check endpoint for container monitoring"""
    try:
        # Check database connection
        connection.ensure_connection()
        return JsonResponse({
            'status': 'healthy',
            'database': 'connected'
        })
    except Exception as e:
        return JsonResponse({
            'status': 'unhealthy',
            'error': str(e)
        }, status=503)

urlpatterns = [
    # Health check endpoint
    path('health/', health_check, name='health_check'),
    
    # Redirect /admin to /myadmin
    path('admin/', RedirectView.as_view(url='/myadmin/', permanent=False)),
    path('myadmin/', include('shop.urls_admin')),
    path('', include('shop.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
