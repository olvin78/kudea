# Panel de administración de Django
from django.contrib import admin

# path crea rutas, include mete las urls de cada app
from django.urls import path, include

# Para servir archivos media cuando DEBUG=True
from django.conf import settings
from django.conf.urls.static import static

# Vistas de fiado (cuenta corriente de cliente)
from applications.customer import views as customer_views



urlpatterns = [

    # ===============================
    # ADMIN
    # ===============================
    # Acceso al panel admin: /admin/
    path('admin/', admin.site.urls),


    # ===============================
    # HOME
    # ===============================
    # Página principal del sistema (raíz del proyecto)
    # Ejemplo: http://localhost:8000/
    path('', include('applications.home.urls')),


    # ===============================
    # APLICACIONES DEL SISTEMA
    # ===============================

    # TPV general
    path('tpv/', include('applications.tpv.urls')),

    # TPV tienda online
    path('tpv_shop/', include('applications.tpv_shop.urls')),

    # Gestión de clientes
    # (ojo: el alta rápida debe ir ANTES del include, si no nunca se llega)
    path('clientes/nuevo-ajax/', customer_views.cliente_ajax, name='cliente_ajax'),
    path('clientes/', include('applications.customer.urls')),

    # ===============================
    # FIADO (cuenta corriente de cliente)
    # ===============================
    # /fiado/                 → deudores, saldo y cobrar
    # /fiado/cobrar/<venta>/  → el cliente paga (total o parcial)
    # /fiado/recibo/<pago>/   → recibo imprimible
    path('fiado/', customer_views.fiado_lista, name='fiado_lista'),
    path('fiado/cobrar/<int:venta_id>/', customer_views.fiado_cobrar, name='fiado_cobrar'),
    path('fiado/recibo/<int:pago_id>/', customer_views.fiado_recibo, name='fiado_recibo'),
    # Alta de cliente independiente (no usa la plantilla de tpv_shop)
    path('fiado/cliente/nuevo/', customer_views.fiado_cliente_nuevo, name='fiado_cliente_nuevo'),

    # Registro de horas
    path('attendance/', include('applications.attendance.urls')),

    # Presupuestos
    path('budget/', include('applications.budget.urls')),

    # Soporte / Tickets
    path('support/', include('applications.support.urls')),

    # Gestión de stock
    path('stock/', include('applications.stock.urls')),

    # Compras y proveedores (módulo purchases)
    path('compras/', include('applications.purchases.urls')),

    # Facturación
    path('invoices/', include('applications.invoice.urls')),

    # Caja
    path('cash/', include('applications.cash.urls')),

    # Informes
    path('reporting/', include('applications.reporting.urls')),

    # Movimientos de caja
    path('cashflow/', include('applications.cashflow.urls')),

    # Formas de pago
    path('payments/', include('applications.payments.urls')),

    # Cuentas contables (Movido de accounts/ a billing/ para evitar conflicto con allauth)
    path('billing/', include('applications.accounts.urls')),

    # Registro de logs
    path('recordlog/', include('applications.recordlog.urls')),

    # Empleados
    path('employees/', include('applications.employee.urls')),

    # Configuraciones del sistema / Panel del Guardián
    path('configuraciones/', include('applications.config.urls')),


    # ===============================
    # AUTHENTICATION (ALLAUTH)
    # ===============================
    path('accounts/', include('allauth.urls')),

]


# ===============================
# MEDIA (solo en desarrollo)
# ===============================
# Permite acceder a archivos subidos (imagenes, pdf, etc.)
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
