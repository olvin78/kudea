from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

from applications import home, support





urlpatterns = [
    path('admin/', admin.site.urls),

    # App principal de la web
    path('', include('applications.home.urls')),

    # Soporte / helpdesk
    path('support/', include('applications.support.urls')),

    # Presupuestos (Budget)
    path('budget/', include('applications.budget.urls', namespace="budget_app")),
]

# Archivos multimedia en desarrollo
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
