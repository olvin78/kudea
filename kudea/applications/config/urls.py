from django.urls import path
from applications.config.views import ConfiguracionesView, RefreshPinView

urlpatterns = [
    path('', ConfiguracionesView.as_view(), name='configuraciones'),
    path('refresh-pin/<int:caja_id>/', RefreshPinView.as_view(), name='refresh_pin'),
]
