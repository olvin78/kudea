from django.urls import path
from . import views
from django.conf import settings
from django.conf.urls.static import static
from .views import CrearCategoriaAjaxView

app_name = 'product_app'

urlpatterns = [
    # Página de inicio
    path('home', views.HomePageView.as_view(), name='home'),
    
    # URLs del TPV
    path('home/productos/', views.ProductoListView.as_view(), name='lista_productos'),
    path('home/productos/crear/', views.CrearProductoView.as_view(), name='crear_producto'),
    path('categoria/ajax/crear/', CrearCategoriaAjaxView.as_view(), name='crear_categoria_ajax'),

]

# Esto va fuera del bloque urlpatterns
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
