# =====================================================================
# 📁 RUTAS · APP 'reporting'  (INFORMES, CONTABILIDAD Y EXPORTES)
# URL base: /reporting/
#   · Dashboard (ventas, donuts, alertas, beneficio)
#   · Contabilidad: P&L + libro de IVA (sobre home.Venta)
#   · Export CSV/XLSX (?fmt=xlsx|csv) — rol gerente
# SE RELACIONA CON: home (Venta/Devolución), cashflow (Movimiento),
#                   purchases (Compras/CxP) — SOLO LEE, no escribe.
# =====================================================================

from django.urls import path
from applications.config.roles import role_required
from .views import DashboardPrincipalView  # ← ESTE ES EL NOMBRE REAL
from .exports import exportar_informe
from .contabilidad import ContabilidadView

app_name = "reporting_app"

urlpatterns = [
    path('', role_required('gerente')(DashboardPrincipalView.as_view()), name="dashboard_informes"),
    path('export/<str:tipo>/', exportar_informe, name="exportar"),
    path('contabilidad/', role_required('gerente')(ContabilidadView.as_view()), name="contabilidad"),
]