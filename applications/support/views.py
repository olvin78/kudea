from django.shortcuts import render
from django.shortcuts import get_object_or_404, redirect
from django.http import HttpResponse
from django.views.generic import TemplateView, CreateView, ListView, DetailView, UpdateView, DeleteView
from django.urls import reverse_lazy
from . models import Ticket  # Asegúrate de importar el modelo 'Ticket'
from django.db.models import Q


# Create your views here.


class CrearTicketView(CreateView):
    model = Ticket
    template_name = 'support/ticket_create.html'
    fields = ['tipo', 'asunto', 'descripcion', 'archivo', 'prioridad']

    def form_valid(self, form):
        form.instance.cliente = self.request.user
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy('support_app:ticket_detail', kwargs={'identificador': self.object.identificador})


class SelectTicketCategoryView(TemplateView):
    template_name = "support/select_ticket_category.html"


class TicketListView(ListView):
    model = Ticket
    template_name = 'support/ticket_list.html'
    context_object_name = 'tickets'
    paginate_by = 10

    def get_queryset(self):
        queryset = super().get_queryset().select_related('cliente')
        query = self.request.GET.get('q')
        if query:
            queryset = queryset.filter(
                Q(identificador__icontains=query) |
                Q(asunto__icontains=query) |
                Q(cliente__username__icontains=query) |
                Q(creado__icontains=query)
            )
        return queryset


class TicketDetailView(DetailView):
    model = Ticket
    template_name = 'support/ticket_detail.html'
    context_object_name = 'ticket'
    slug_field = 'identificador'
    slug_url_kwarg = 'identificador'





class TicketUpdateView(UpdateView):
    model = Ticket
    fields = ['tipo', 'asunto', 'descripcion', 'archivo', 'estado', 'prioridad']
    template_name = 'support/ticket_update.html'
    context_object_name = 'ticket'

    def get_success_url(self):
        return reverse_lazy('support_app:ticket_detail', kwargs={'identificador': self.object.identificador})




class TicketDeleteView(DeleteView):
    model = Ticket
    template_name = 'support/ticket_confirm_delete.html'
    context_object_name = 'ticket'
    slug_field = 'identificador'
    slug_url_kwarg = 'identificador'

    def get_success_url(self):
        return reverse_lazy('support_app:ticket_list')
