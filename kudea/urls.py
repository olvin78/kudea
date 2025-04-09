from django.contrib import admin
from django.urls import path, include
from applications import home

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('applications.home.urls')),
    
    # ✅ AÑADE ESTA LÍNEA:
    path('tpv/', include('applications.tpv.urls')),
]
