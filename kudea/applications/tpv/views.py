# tpv/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from django.views.generic import TemplateView, ListView, CreateView, DetailView, UpdateView, DeleteView, FormView
from django.db import models
from django.urls import reverse_lazy
from .models import Mesa, Comanda, ComandaItem, Empleado  # Importando los modelos necesarios
from applications.product.models import Producto, Categoria
from .forms import ComandaItemForm, ComandaForm, EmpleadoForm # Importando los formularios necesarios
from applications.product.forms import ProductoForm
from django.http import JsonResponse
from applications.tpv.models import Mesa, Comanda  # ajusta si tu modelo está en otro lugar

from applications.home.models import MetodoPago  # <--- aquí corregido
from applications.payments.models import MetodoPago


class TpvIndexView(TemplateView):
    template_name = 'tpv/index.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['mesas'] = Mesa.objects.all()
        context['comandas'] = Comanda.objects.filter(estado='abierta')
        context['products'] = Producto.objects.all()
        
        # 🔽 AÑADE ESTO para cargar los métodos de pago
        context['metodos_pago'] = MetodoPago.objects.all()

        # Datos para el resumen del día
        context['mesas_ocupadas'] = Mesa.objects.filter(estado='ocupada').count()
        context['mesas_totales'] = Mesa.objects.count()
        context['ventas_totales'] = Comanda.objects.filter(estado='abierta').aggregate(total=models.Sum('total'))['total'] or 0
        context['comandas_abiertas'] = Comanda.objects.filter(estado='abierta').count()
        context['porcentaje_ocupacion'] = int(context['mesas_ocupadas'] * 100 / context['mesas_totales']) if context['mesas_totales'] > 0 else 0

        return context


class TpvMesasView(ListView):
    model = Mesa
    template_name = 'tpv/mesas.html'
    context_object_name = 'mesas'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['comandas'] = Comanda.objects.filter(estado='abierta')
        context['mesas_ocupadas'] = Mesa.objects.filter(estado='ocupada').count()
        context['mesas_totales'] = Mesa.objects.count()
        context['ventas_totales'] = sum(c.total for c in Comanda.objects.filter(estado='abierta'))
        context['comandas_abiertas'] = Comanda.objects.filter(estado='abierta').count()
        if context['mesas_totales'] > 0:
            context['porcentaje_ocupacion'] = (context['mesas_ocupadas'] / context['mesas_totales']) * 100
        else:
            context['porcentaje_ocupacion'] = 0
        return context



class MesaCreateView(CreateView):
    model = Mesa
    fields = ['nombre', 'estado', 'capacidad']
    template_name = 'tpv/mesa_form.html'
    success_url = reverse_lazy('tpv_app:tpv_mesas')  # <--- Así, usando el namespace correcto



class MesaDetailView(DetailView):
    model = Mesa
    template_name = 'tpv/mesa_categorias.html'
    context_object_name = 'mesa'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        mesa = self.object

        # Obtener las categorías y productos
        context['categories'] = Categoria.objects.all()
        
        # Obtener el parámetro de filtro de categoría (si lo hay)
        category_slug = self.request.GET.get('category', None)
        
        # Filtrar los productos si se pasa el slug de categoría
        if category_slug:
            context['products'] = Producto.objects.filter(category__slug=category_slug)
        else:
            context['products'] = Producto.objects.all()  # Si no hay filtro, mostrar todos

        # Buscar la comanda abierta
        comanda_abierta = mesa.comandas.filter(estado='abierta').first()

        if comanda_abierta:
            cart_items = comanda_abierta.items.all()
            total_price = sum(item.subtotal() for item in cart_items)
        else:
            cart_items = []
            total_price = 0

        context['cart_items'] = cart_items
        context['total_price'] = total_price

        return context



class MesaCategoriasView(View):
    def get(self, request, mesa_id):
        mesa = get_object_or_404(Mesa, pk=mesa_id)

        # Obtener o crear una comanda abierta para esta mesa
        comanda, created = Comanda.objects.get_or_create(mesa=mesa, estado='abierta')

        categorias = Categoria.objects.all()

        return render(request, 'tpv/mesa_categorias.html', {
            'mesa': mesa,
            'comanda': comanda,
            'categories': categorias,
        })



class MesaProductosPorCategoriaView(TemplateView):
    template_name = 'tpv/productos_por_categoria.html'  # Asegúrate que es el correcto

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        mesa_id = self.kwargs.get('mesa_id')
        categoria_id = self.kwargs.get('categoria_id')

        context['mesa'] = Mesa.objects.get(id=mesa_id)
        context['productos'] = Producto.objects.filter(categoria_id=categoria_id, activo=True)
        context['metodos_pago'] = MetodoPago.objects.filter(activo=True)
        context['metodo_pago_seleccionado'] = None  # Puedes rellenar si haces selección persistente

        return context

class AgregarProductoAComandaView(View):
    def post(self, request, comanda_id):
        comanda = get_object_or_404(Comanda, id=comanda_id)
        producto_id = request.POST.get('producto_id')
        producto = get_object_or_404(Producto, id=producto_id)

        item, created = ComandaItem.objects.get_or_create(
            comanda=comanda,
            producto=producto,
            defaults={'cantidad': 1, 'precio_unitario': producto.precio}
        )
        if not created:
            item.cantidad += 1
            item.save()

        comanda.calcular_total()
        return redirect(request.META.get('HTTP_REFERER', '/'))




class MesaComandaActivaRedirectView(View):
    def get(self, request, mesa_id):
        mesa = get_object_or_404(Mesa, pk=mesa_id)
        comanda = Comanda.objects.filter(mesa=mesa, estado='abierta').first()

        if comanda:
            return redirect('tpv_app:comanda_detail', pk=comanda.pk)
        else:
            nueva_comanda = Comanda.objects.create(mesa=mesa, estado='abierta', usuario=request.user)
            return redirect('tpv_app:comanda_detail', pk=nueva_comanda.pk)


class MesaUpdateView(UpdateView):
    model = Mesa
    fields = ['nombre', 'capacidad', 'estado']  # o los campos que quieras editar
    template_name = 'tpv/mesa_form.html'
    success_url = reverse_lazy('tpv_app:tpv_mesas')



class MesaDeleteView(DeleteView):
    model = Mesa
    template_name = 'tpv/mesa_confirm_delete.html'  # Esta plantilla la creamos ahora
    success_url = reverse_lazy('tpv_app:tpv_mesas')
    context_object_name = 'mesa'



class ToggleMesaEstadoView(View):
    def post(self, request, pk):
        mesa = get_object_or_404(Mesa, pk=pk)
        if mesa.estado == 'libre':
            mesa.estado = 'ocupada'
        else:
            mesa.estado = 'libre'
        mesa.save()
        return redirect('tpv_app:tpv_mesas')




# Vista para crear una nueva comanda
class ComandaCreateView(CreateView):
    model = Comanda
    form_class = ComandaForm  # Usar el formulario ComandaForm
    template_name = 'tpv/create_comanda.html'
    context_object_name = 'form'

    def form_valid(self, form):
        form.instance.mesa = form.cleaned_data['mesa']
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy('tpv_app:comanda_detail', kwargs={'pk': self.object.pk})




class ComandaDetailView(DetailView):
    model = Comanda
    template_name = 'tpv/comanda_detail.html'
    context_object_name = 'comanda'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['items'] = self.object.items.all()
        context['total'] = self.object.calcular_total()
        return context




class ComandaListView(ListView):
    model = Comanda
    template_name = 'tpv/comanda_list.html'  # Ahora te paso también esta plantilla
    context_object_name = 'comandas'




class ComandaCerrarView(View):
    def post(self, request, pk, *args, **kwargs):
        comanda = get_object_or_404(Comanda, pk=pk)
        comanda.estado = 'cerrada'
        comanda.save()
        return redirect('tpv_app:tpv_comandas')  # O donde quieras redirigir después de cerrar
        


class AgregarProductoACamadaView(FormView):
    template_name = 'comanda/agregar_producto.html'
    form_class = ComandaItemForm
    
    def get_comanda(self):
        comanda_id = self.kwargs.get('comanda_id')
        return get_object_or_404(Comanda, id=comanda_id)
    
    def form_valid(self, form):
        comanda = self.get_comanda()
        nuevo_item = form.save(commit=False)
        nuevo_item.comanda = comanda
        nuevo_item.save()
        
        # Actualizar el total de la comanda
        comanda.calcular_total()
        
        # Redirigir a los detalles de la comanda
        return redirect('comanda:detalles', comanda_id=comanda.id)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['comanda'] = self.get_comanda()
        return context



class ComandaDetailView(DetailView):
    model = Comanda
    template_name = 'tpv/comanda_detail.html'
    context_object_name = 'comanda'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['items'] = self.object.items.all()
        context['total'] = self.object.calcular_total()
        return context





class ProductFilterView(ListView):
    model = Producto
    template_name = 'tpv/product_filter.html'  # Asegúrate de que esta plantilla exista
    context_object_name = 'products'

    def get_queryset(self):
        category = self.kwargs['category']
        return Producto.objects.filter(category=category)  # Filtra por categoría


class TpvComandasView(TemplateView):
    template_name = 'tpv/comandas.html'



class TpvCobrosView(TemplateView):
    template_name = 'tpv/cobros.html'

class TpvHistorialView(TemplateView):
    template_name = 'tpv/historial.html'

class TpvConfigView(TemplateView):
    template_name = 'tpv/config.html'



class EmpleadoCreateView(CreateView):
    model = Empleado
    fields = [
        'nombre', 'apellidos', 'nif', 'usuario', 'email', 'telefono', 'movil',
        'direccion', 'cp', 'poblacion', 'provincia', 'es_administrador',
        'puede_realizar_salidas', 'puede_cambiar_fecha_hora', 'puede_modificar_ventas',
        'puede_cambiar_subtotales', 'puede_cambiar_tarifa', 'esta_de_baja', 'fecha_baja',
        'observaciones'
    ]
    template_name = 'tpv/empleado_create.html'
    success_url = reverse_lazy('tpv_app:empleados_lista')  # Ajusta este nombre si tu lista de empleados tiene otro




# Vista para mostrar la lista de empleados
class EmpleadoListView(ListView):
    model = Empleado
    template_name = 'tpv/empleados_lista.html'  # Asegúrate de que la plantilla exista
    context_object_name = 'empleados'
    paginate_by = 10  # Si deseas paginación

# Vista para editar un empleado
class EmpleadoUpdateView(UpdateView):
    model = Empleado
    form_class = EmpleadoForm
    template_name = 'tpv/editar_empleado.html'  # Asegúrate de que la plantilla exista
    context_object_name = 'empleado'

    def get_success_url(self):
        return reverse_lazy('tpv_app:empleados_lista')  # Redirige a la lista de empleados tras guardar



class ProductListView(ListView):
    model = Producto
    template_name = 'home/product_list.html'
    context_object_name = 'products'


class ProductCreateView(CreateView):
    model = Producto
    form_class = ProductoForm
    template_name = 'tpv/product_form.html'
    success_url = reverse_lazy('tpv_app:product_list')

class ProductUpdateView(UpdateView):
    model = Producto
    form_class = ProductoForm
    template_name = 'tpv/product_form.html'
    success_url = reverse_lazy('tpv_app:product_list')
    
    def get_object(self,):
        pk = self.kwargs.get('pk')
        print(f"DEBUG: Editing product with pk={pk}")
        return get_object_or_404(Producto, pk=pk)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['titulo'] = 'Editar Producto'
        context['producto'] = self.object
        print(f"DEBUG: producto={self.object}, form={context.get('form')}")
        return context

class ProductDeleteView(DeleteView):
    model = Producto
    success_url = reverse_lazy('tpv_app:product_list')

    def get(self, request, *args, **kwargs):
        return self.post(request, *args, **kwargs)