# Django imports
from django.shortcuts import render
from django.http import JsonResponse
from django.views.generic import TemplateView, CreateView, ListView, View
from django.urls import reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import transaction, models
from django.utils.text import slugify
import random
import string

# Proyecto imports
from .models import Producto, Venta, DetalleVenta, Categoria, MetodoPago, ConfiguracionTPV
from .forms import ProductoForm

class HomePageView(TemplateView):
    template_name = 'home/index.html'

class TPVView(LoginRequiredMixin, TemplateView):
    template_name = 'home/index.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['productos'] = Producto.objects.filter(activo=True).order_by('nombre')
        context['categorias'] = Categoria.objects.all().order_by('nombre')
        context['metodos_pago'] = MetodoPago.objects.filter(activo=True)
        context['config'] = ConfiguracionTPV.objects.first()
        context['current_user'] = self.request.user
        return context



class CrearCategoriaAjaxView(LoginRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        import json
        data = json.loads(request.body)
        nombre = data.get("nombre")
        descripcion = data.get("descripcion", "")

        if not nombre:
            return JsonResponse({"success": False, "error": "Nombre requerido"}, status=400)

        if Categoria.objects.filter(nombre__iexact=nombre).exists():
            return JsonResponse({"success": False, "error": "Ya existe una categoría con ese nombre"}, status=400)

        categoria = Categoria.objects.create(nombre=nombre, descripcion=descripcion, slug=slugify(nombre))
        return JsonResponse({"success": True, "id": categoria.id, "nombre": categoria.nombre})



class ProductoListView(LoginRequiredMixin, ListView):
    model = Producto
    template_name = 'home/product_list.html'
    context_object_name = 'productos'
    paginate_by = 20
    
    def get_queryset(self):
        queryset = super().get_queryset().filter(activo=True)
        search = self.request.GET.get('search', '')
        categoria_id = self.request.GET.get('categoria_id', None)
        
        if search:
            queryset = queryset.filter(
                models.Q(nombre__icontains=search) | 
                models.Q(codigo_barras__icontains=search)
            )
        
        if categoria_id and categoria_id != '0':
            queryset = queryset.filter(categoria_id=categoria_id)
        
        return queryset.order_by('nombre')



class CrearProductoView(LoginRequiredMixin, CreateView):
    model = Producto
    form_class = ProductoForm
    template_name = 'home/crear_producto.html'
    
    def get_initial(self):
        initial = super().get_initial()
        # Generar código automático para mostrarlo directamente
        while True:
            new_code = 'KUD-' + ''.join(random.choices(string.digits, k=8))
            if not Producto.objects.filter(codigo_barras=new_code).exists():
                initial['codigo_barras'] = new_code
                break
        return initial

    def get_success_url(self):
        return reverse_lazy('home_app:lista_productos')  # Redirige a la lista de empleados tras guardar


