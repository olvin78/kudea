# =====================================================================
# 📁 RUTAS · APP 'stock'  (ALMACÉN — movimientos de stock)
# URL base: /stock/
#   · Entradas/salidas de mercancía (Movement), informe y PDF
#   · Compras recibidas rellenan Producto.costo desde aquí
# SE RELACIONA CON:
#   · product (Movement→Producto)  · purchases (recepción de compra)
#   · home (las ventas TPV descuentan stock automáticamente)
# =====================================================================

from django.urls import path
from . import views

app_name = 'stock_app'

urlpatterns = [
    path('', views.MovementListView.as_view(), name='movement_list'),
    path('crear/', views.movement_create, name='movement_create'),
    path('informe-data/', views.informe_inventario_data, name='informe_inventario_data'),
    path('informe-pdf/', views.informe_inventario_pdf, name='informe_inventario_pdf'),
]