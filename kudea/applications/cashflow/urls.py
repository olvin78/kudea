# =====================================================================
# 📁 RUTAS · APP 'cashflow'  (MOVIMIENTOS DE CAJA UNIFICADOS)
# URL base: /cashflow/
#   · Toda la entrada/salida de dinero con su Cuenta
#   · external_ref enlaza con el origen:
#       tpv:venta:<id>[:efectivo|:tarjeta]   → venta TPV (property venta_pk)
#       fiado:pago:<id>                      → cobro de fiado
#       compra:<pk>:pago:<pago_pk>           → pago a proveedor
#       devolucion:<id>                      → devolución
# SE RELACIONA CON: home, customer, purchases, payments (referencias)
# =====================================================================

from django.urls import path
from applications.config.roles import role_required
from . import views

app_name = 'cashflow'

G = role_required('gerente')

urlpatterns = [
    # Listado principal
    path('', G(views.CashflowListView.as_view()), name='movement_list'),

    # AJAX para crear movimiento
    path('crear-movimiento/', G(views.crear_movimiento_ajax), name='crear_movimiento_ajax'),

    # AJAX para obtener detalle rápido (para el modal)
    path('movimiento/<int:movimiento_id>/detalle/', G(views.detalle_movimiento_api), name='detalle_movimiento_api'),

    # AJAX para forzar el cierre de una caja por parte del admin
    path('caja/forzar-cierre/', G(views.force_close_register_ajax), name='force_close_register_ajax'),

    # Página de detalle completo (tipo factura) - DONDE LLEVA "VER MÁS DETALLES"
    path('movimiento/<int:pk>/', G(views.MovimientoDetailView.as_view()), name='detalle_completo'),
]