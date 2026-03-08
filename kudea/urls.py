# Panel de administración de Django
from django.contrib import admin

# path crea rutas, include mete las urls de cada app
from django.urls import path, include

# Para servir archivos media cuando DEBUG=True
from django.conf import settings
from django.conf.urls.static import static

# Vista de login incluida en Django
from django.contrib.auth import views as auth_views


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
    path('clientes/', include('applications.customer.urls')),

    # Registro de horas
    path('attendance/', include('applications.attendance.urls')),

    # Presupuestos
    path('budget/', include('applications.budget.urls')),

    # Soporte / Tickets
    path('support/', include('applications.support.urls')),

    # Gestión de stock
    path('stock/', include('applications.stock.urls')),

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

    # Cuentas contables
    path('accounts/', include('applications.accounts.urls')),

    # Registro de logs
    path('recordlog/', include('applications.recordlog.urls')),

    # Empleados
    path('employees/', include('applications.employee.urls')),

    # Configuraciones del sistema / Panel del Guardián
    path('configuraciones/', include('applications.config.urls')),


    # ===============================
    # LOGIN
    # ===============================
    # Página de login
    path('login/', auth_views.LoginView.as_view(), name='login'),
]


# ===============================
# MEDIA (solo en desarrollo)
# ===============================
# Permite acceder a archivos subidos (imagenes, pdf, etc.)
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)