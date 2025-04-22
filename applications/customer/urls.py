from django.urls import path
from . import views

app_name = 'customer_app'

urlpatterns = [
    path('nuevo/', views.CustomerCreateView.as_view(), name='create'),  # Asegúrate de que esta URL sea correcta
    path('search/', views.search_cliente, name='search_cliente'),  # Nueva ruta para búsqueda de clientes
]
