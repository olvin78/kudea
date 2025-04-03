from django.shortcuts import render
from django.http import HttpResponse
from django.views.generic import TemplateView, CreateView
from django.urls import reverse_lazy
from .models import Ticket  # Asegúrate de importar el modelo 'Ticket'


class HomePageView(TemplateView):
    template_name = 'home/index.html'  # Asegúrate de que esta ruta sea correcta

# Vista para crear un nuevo ticket
class CrearTicketView(CreateView):
    model = Ticket
    template_name = 'home/crear_ticket.html'  # Ruta al template de creación de ticket
    fields = ['campo1', 'campo2', 'campo3']  # Los campos que deseas que el formulario contenga
    success_url = reverse_lazy('ticket_exito')  # Redirige después de crear el ticket



class CrearTicketView(CreateView):
    model = Ticket  # Ahora Ticket está correctamente definido
    template_name = 'crear_ticket.html'  # El template donde se mostrará el formulario
    fields = ['campo1', 'campo2', 'campo3']  # Los campos que deseas que el formulario contenga
    success_url = reverse_lazy('nombre_de_la_url_de_exito')  # Redirige después de crear el objeto

    def form_valid(self, form):
        # Lógica adicional antes de guardar el formulario (si es necesario)
        return super().form_valid(form)





class SelectTicketCategoryView(TemplateView):
    template_name = "home/select_ticket_category.html"
