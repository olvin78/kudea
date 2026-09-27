# ============================================================
# RUTAS DEL MÓDULO DE COMPRAS (app: purchases)
#   /compras/                          → lista de compras
#   /compras/nueva/                    → crear compra (cabecera + líneas)
#   /compras/<id>/                     → detalle de la compra
#   /compras/<id>/recibir/             → recibir mercancía (sube stock)
#   /compras/<id>/cancelar/            → cancelar compra
#   /compras/proveedores/              → lista de proveedores
#   /compras/proveedores/nuevo/        → alta de proveedor
#   /compras/proveedores/<id>/editar/  → edición de proveedor
# ============================================================
from django.urls import path

from . import views

app_name = 'purchases_app'

urlpatterns = [
    # ---- 1) COMPRAS ----
    path('', views.CompraListView.as_view(), name='compra_list'),
    path('nueva/', views.CompraCreateView.as_view(), name='compra_create'),
    path('<int:pk>/', views.CompraDetailView.as_view(), name='compra_detail'),
    path('<int:pk>/recibir/', views.compra_recibir, name='compra_recibir'),
    path('<int:pk>/cancelar/', views.compra_cancelar, name='compra_cancelar'),

    # ---- 2) PROVEEDORES ----
    path('proveedores/', views.ProveedorListView.as_view(), name='proveedor_list'),
    path('proveedores/nuevo/', views.ProveedorCreateView.as_view(), name='proveedor_create'),
    path('proveedores/<int:pk>/editar/', views.ProveedorUpdateView.as_view(), name='proveedor_update'),

    # ---- 5) PDF DE PEDIDO DE REPOSICIÓN (agrupado por proveedor) ----
    path('pedido-pdf/', views.pedido_pdf, name='pedido_pdf'),

    # ---- 6) INFORMES (gasto por proveedor + margen por producto) ----
    path('informes/', views.informe_compras, name='informe_compras'),
]
