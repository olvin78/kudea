from django.urls import path
from applications.config.views import ConfiguracionesView

urlpatterns = [
    path('', ConfiguracionesView.as_view(), name='configuraciones'),
]
