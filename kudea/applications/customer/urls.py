# =====================================================================
# 📁 RUTAS · APP 'customer'  (CLIENTES + FIADO)
# URL base: /clientes/  y  /fiado/
#   · Lista y ficha de cliente (CRM: gasto, historial, cuenta corriente)
#   · Fiado: deudores, cobros parciales, recibos, alta de cliente
#   · Usa customer.Cliente — el cliente COMÚN del TPV, fiado y CRM
# SE RELACIONA CON:
#   · home (Venta.cliente → Cliente; PagoFiado→Venta)
#   · payments (método del cobro)
# OJO: budget (presupuestos) e invoice (facturas) NO usan este cliente.
# =====================================================================

from django.urls import path
from . import views

app_name = 'customer_app'

urlpatterns = [
    path('', views.ListaClientesView.as_view(), name='lista'),
    path('<int:pk>/', views.FichaClienteView.as_view(), name='ficha'),
    path('nuevo/', views.CustomerCreateView.as_view(), name='create'),  # Asegúrate de que esta URL sea correcta
    path('search/', views.search_cliente, name='search_cliente'),  # Nueva ruta para búsqueda de clientes
]
