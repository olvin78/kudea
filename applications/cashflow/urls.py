from django.urls import path
from . import views

app_name = 'cashflow'

urlpatterns = [
    # Listado principal
    path('', views.CashflowListView.as_view(), name='movement_list'),

    # AJAX para crear movimiento
    path('crear-movimiento/', views.crear_movimiento_ajax, name='crear_movimiento_ajax'),

    # AJAX para obtener detalle rápido (para el modal)
    path('movimiento/<int:movimiento_id>/detalle/', views.detalle_movimiento_api, name='detalle_movimiento_api'),

    # Página de detalle completo (tipo factura) - DONDE LLEVA "VER MÁS DETALLES"
    path('movimiento/<int:pk>/', views.MovimientoDetailView.as_view(), name='detalle_completo'),
]