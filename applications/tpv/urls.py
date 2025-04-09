from django.urls import path
from .views import (
    TpvIndexView,
    TpvMesasView,
    TpvComandasView,
    TpvCobrosView,
    TpvHistorialView,
    TpvConfigView,
)

app_name = 'tpv_app'

urlpatterns = [
    path('', TpvIndexView.as_view(), name='tpv_index'),
    path('mesas/', TpvMesasView.as_view(), name='tpv_mesas'),
    path('comandas/', TpvComandasView.as_view(), name='tpv_comandas'),
    path('cobros/', TpvCobrosView.as_view(), name='tpv_cobros'),
    path('historial/', TpvHistorialView.as_view(), name='tpv_historial'),
    path('config/', TpvConfigView.as_view(), name='tpv_config'),
]