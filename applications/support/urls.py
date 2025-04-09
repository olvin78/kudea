from django.urls import path,include
from . import views  # Asegúrate de importar views correctamente
from .views import CrearTicketView, TemplateView, SelectTicketCategoryView,TicketListView,TicketDetailView, TicketUpdateView, TicketDeleteView # Importar la vista CrearTicketView


app_name = 'support_app'

urlpatterns = [
    path('crear_ticket/', views.CrearTicketView.as_view(), name='crear_ticket'),  # Crear ticket
    path('ticket_exito/', TemplateView.as_view(template_name='ticket_exito.html'), name='ticket_exito'),
    path('select-ticket-category/', SelectTicketCategoryView.as_view(), name='select_ticket_category'),
    path('tickets/', TicketListView.as_view(), name='ticket_list'),
    path('tickets/<str:identificador>/', TicketDetailView.as_view(), name='ticket_detail'),
    path('tickets/<int:pk>/editar/', TicketUpdateView.as_view(), name='ticket_edit'),# 👈 NUEVA
    path('tickets/<str:identificador>/eliminar/', TicketDeleteView.as_view(), name='ticket_delete'),



]