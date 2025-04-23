from django.contrib import admin

from django.urls import path
from django.urls import include
from applications import home,tpv,tpv_shop,customer
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('applications.home.urls')),  # Mantén tu aplicación dentro de i18n_patterns
    path('tpv/', include('applications.tpv.urls')),  # Asegúrate de que esta línea esté aquí
    path('tpv_shop/', include('applications.tpv_shop.urls')),  # Agregar ruta para la tienda
    path('clientes/', include('applications.customer.urls')),  # Incluye las URLs de customer
    path('login/', auth_views.LoginView.as_view(), name='login'),

]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
