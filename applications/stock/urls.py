from django.urls import path
from . import views

app_name = 'stock_app'

urlpatterns = [
    path('', views.MovementListView.as_view(), name='movement_list'),
    path('crear/', views.movement_create, name='movement_create'),
    path('informe-data/', views.informe_inventario_data, name='informe_inventario_data'),
    path('informe-pdf/', views.informe_inventario_pdf, name='informe_inventario_pdf'),
]