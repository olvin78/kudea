from django.urls import path
from . import views  # Asegúrate de importar views correctamente
from .views import HomePageView, CrearTicketView,TemplateView,SelectTicketCategoryView  # Importar la vista CrearTicketView

urlpatterns = [
    path('', views.HomePageView.as_view(), name='home'),  # Página de inicio
    path('crear_ticket/', views.CrearTicketView.as_view(), name='crear_ticket'),  # Crear ticket
    path('ticket_exito/', TemplateView.as_view(template_name='ticket_exito.html'), name='ticket_exito'),
    path('select-ticket-category/', SelectTicketCategoryView.as_view(), name='select_ticket_category'),
    # Página de éxito
]
