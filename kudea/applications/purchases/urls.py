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

from applications.config.roles import role_required
from . import views

app_name = 'purchases_app'

G = role_required('gerente')

urlpatterns = [
    # ---- 1) COMPRAS ----
    path('', G(views.CompraListView.as_view()), name='compra_list'),
    path('nueva/', G(views.CompraCreateView.as_view()), name='compra_create'),
    path('<int:pk>/', G(views.CompraDetailView.as_view()), name='compra_detail'),
    path('<int:pk>/recibir/', G(views.compra_recibir), name='compra_recibir'),
    path('<int:pk>/cancelar/', G(views.compra_cancelar), name='compra_cancelar'),
    path('<int:pk>/pagar/', G(views.compra_pagar), name='compra_pagar'),

    # ---- 2) PROVEEDORES ----
    path('proveedores/', G(views.ProveedorListView.as_view()), name='proveedor_list'),
    path('proveedores/nuevo/', G(views.ProveedorCreateView.as_view()), name='proveedor_create'),
    path('proveedores/<int:pk>/editar/', G(views.ProveedorUpdateView.as_view()), name='proveedor_update'),

    # ---- 5) PDF DE PEDIDO DE REPOSICIÓN (agrupado por proveedor) ----
    path('pedido-pdf/', G(views.pedido_pdf), name='pedido_pdf'),

    # ---- 6) INFORMES (gasto por proveedor + margen por producto) ----
    path('informes/', G(views.informe_compras), name='informe_compras'),
]
