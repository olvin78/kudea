from django.urls import path
from .views import CashIndexView, AperturaCajaView, PauseCajaView

app_name = "cash_app"

urlpatterns = [
    path("", CashIndexView.as_view(), name="cash_index"),
    path("apertura/", AperturaCajaView.as_view(), name="apertura_caja"),
    path("pausar/", PauseCajaView.as_view(), name="pausar_caja"),
]
