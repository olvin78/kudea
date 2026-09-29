# =====================================================================
# 📁 RUTAS · APP 'cash'  (CIERRE/ARQUEO DE CAJA)
# URL base: /cash/
#   · Apertura, cierre y arqueo de caja (esperado/contado/diferencia)
# SE RELACIONA CON:
#   · cashflow (lee los Movimientos del día para cuadrar)
#   · home (CajaArqueo del TPV de tienda)
# =====================================================================

from django.urls import path
from applications.config.roles import role_required
from .views import CashIndexView, AperturaCajaView, PauseCajaView, CierreCajaView

app_name = "cash_app"

O = role_required('cajero', 'gerente')  # operador: cajero o mejor

urlpatterns = [
    path("", CashIndexView.as_view(), name="cash_index"),
    path("apertura/", O(AperturaCajaView.as_view()), name="apertura_caja"),
    path("pausar/", O(PauseCajaView.as_view()), name="pausar_caja"),
    path("cierre/", O(CierreCajaView.as_view()), name="cierre_caja"),
]
