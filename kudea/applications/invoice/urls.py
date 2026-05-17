from django.urls import path
from .views import (
    FacturaListView,
    FacturaDetailView,
    FacturaCreateView,
    FacturaUpdateView,
    FacturaDeleteView,
    anular_factura,
)

app_name = 'invoice_app'

urlpatterns = [
    path('', FacturaListView.as_view(), name='invoice_list'),
    path('nueva/', FacturaCreateView.as_view(), name='crear'),
    path('<int:pk>/', FacturaDetailView.as_view(), name='detalle'),
    path('<int:pk>/editar/', FacturaUpdateView.as_view(), name='editar'),
    path('<int:pk>/eliminar/', FacturaDeleteView.as_view(), name='eliminar'),
    path('<int:pk>/anular/', anular_factura, name='anular'),
]
