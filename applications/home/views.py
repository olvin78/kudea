from django.shortcuts import render
from django.http import HttpResponse
from django.views.generic import TemplateView, CreateView, ListView
from django.urls import reverse_lazy


class HomePageView(TemplateView):
    template_name = 'home/index.html'  # Asegúrate de que esta ruta sea correcta

