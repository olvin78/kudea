from django.contrib import admin
from django.urls import path
from django.urls import include
from applications import home


urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('applications.home.urls')),  # Mantén tu aplicación dentro de i18n_patterns
]
