from django.shortcuts import render, redirect
from django.views.generic.edit import CreateView
from .models import Cliente
from .forms import ClienteForm
from django.urls import reverse_lazy
from django.http import JsonResponse




class CustomerCreateView(CreateView):
    model = Cliente
    form_class = ClienteForm
    template_name = 'customer/nuevo_cliente.html'
    success_url = reverse_lazy('tpv_shop:home')  # Redirige al home después de guardar

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form_title'] = 'Crear un nuevo cliente'
        return context

    # Buscar cliente por DNI (para autocompletar)
    def get(self, request, *args, **kwargs):
        dni = request.GET.get('dni')
        if dni:
            try:
                cliente = Cliente.objects.get(dni=dni)
                return JsonResponse({'nombre': cliente.nombre, 'codigo_postal': cliente.codigo_postal, 'correo': cliente.correo, 'telefono': cliente.telefono})
            except Cliente.DoesNotExist:
                return JsonResponse({'error': 'Cliente no encontrado'}, status=404)
        return super().get(request, *args, **kwargs)


def search_cliente(request):
    dni = request.GET.get('dni', None)
    if dni:
        try:
            cliente = Cliente.objects.get(dni=dni)
            data = {
                'found': True,
                'cliente': {
                    'nombre': cliente.nombre,
                    'dni': cliente.dni,
                    'codigo_postal': cliente.codigo_postal,
                    'correo': cliente.correo,
                    'telefono': cliente.telefono
                }
            }
        except Cliente.DoesNotExist:
            data = {'found': False}
    else:
        data = {'found': False}
    
    return JsonResponse(data)
