# =====================================================================
# 📁 RUTAS · APP 'product'  (CATÁLOGO DE PRODUCTOS)
# URL base: varía (incluida desde home/ y tpv/)
#   · Modelo Producto y Categoria — el catálogo COMPARTIDO por todos
# SE RELACIONA CON:
#   · purchases (Producto.proveedor → Proveedor)
#   · Usado por: home.Venta, tpv.ComandaItem, invoice.ItemFactura,
#     stock.Movement, purchases.CompraItem, tpv_shop.CartItem
# =====================================================================

from django.urls import path
from . import views
from django.conf import settings
from django.conf.urls.static import static
from .views import CrearCategoriaAjaxView
from applications.config.roles import role_required

app_name = 'product_app'

urlpatterns = [
    # Página de inicio
    path('home', views.HomePageView.as_view(), name='home'),
    
    # URLs del TPV
    path('home/productos/', views.ProductoListView.as_view(), name='lista_productos'),
    path('home/productos/crear/', role_required('gerente')(views.CrearProductoView.as_view()), name='crear_producto'),
    path('categoria/ajax/crear/', role_required('gerente')(CrearCategoriaAjaxView.as_view()), name='crear_categoria_ajax'),

]

# Esto va fuera del bloque urlpatterns
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
