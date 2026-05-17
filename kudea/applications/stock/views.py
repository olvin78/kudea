from django.views.generic import ListView
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_protect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.db.models import F, Sum, Q
from django.utils import timezone
from applications.product.models import Producto
from .models import Movement


class MovementListView(ListView):
    model = Movement
    template_name = 'stock/movement_list.html'
    context_object_name = 'movements'
    paginate_by = 25

    def get_queryset(self):
        queryset = super().get_queryset()
        search = self.request.GET.get('search', '')
        categoria_id = self.request.GET.get('categoria_id')

        if search:
            queryset = queryset.filter(
                Q(producto__nombre__icontains=search) |
                Q(producto__codigo_barras__icontains=search)
            )
        
        if categoria_id:
            queryset = queryset.filter(producto__categoria_id=categoria_id)
            
        return queryset

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        
        # Filtros
        search = self.request.GET.get('search', '')
        categoria_id = self.request.GET.get('categoria_id')

        productos = Producto.objects.filter(activo=True).order_by('nombre')
        
        if search:
            productos = productos.filter(
                Q(nombre__icontains=search) | Q(codigo_barras__icontains=search)
            )
        
        if categoria_id:
            productos = productos.filter(categoria_id=categoria_id)

        ctx['productos'] = productos
        ctx['title'] = 'Movimientos de stock'

        # Productos con stock bajo (para la sección urgente)
        productos_bajo = productos.filter(stock__lt=F('stock_minimo'))
        ctx['productos_stock_bajo'] = productos_bajo.order_by('stock')
        ctx['productos_bajo_count'] = productos_bajo.count()

        # Estadísticas globales (usamos el queryset filtrado para que las estadísticas coincidan con lo que se ve)
        ctx['total_productos_count'] = productos.count()
        ctx['total_stock'] = productos.aggregate(total=Sum('stock'))['total'] or 0
        ctx['valor_total_stock'] = productos.aggregate(
            total=Sum(F('stock') * F('costo'))
        )['total'] or 0

        # Categorías para el filtro
        from applications.product.models import Categoria
        ctx['categorias'] = Categoria.objects.all().order_by('nombre')

        return ctx


@csrf_protect
@require_POST
@login_required
def movement_create(request):
    producto_id = request.POST.get('producto_id')
    tipo = request.POST.get('tipo')
    cantidad = request.POST.get('cantidad')
    observaciones = (request.POST.get('observaciones') or '').strip()

    if not (producto_id and producto_id.isdigit()):
        return JsonResponse({'ok': False, 'error': 'Producto inválido'}, status=400)

    if tipo not in ('entrada', 'salida'):
        return JsonResponse({'ok': False, 'error': 'Tipo inválido'}, status=400)

    try:
        cantidad = int(cantidad)
        assert cantidad > 0
    except:
        return JsonResponse({'ok': False, 'error': 'Cantidad inválida'}, status=400)

    producto = Producto.objects.get(pk=int(producto_id))

    try:
        m = Movement.objects.create(
            producto=producto,
            cantidad=cantidad,
            tipo=tipo,
            observaciones=observaciones
        )
    except ValueError as e:
        return JsonResponse({'ok': False, 'error': str(e)}, status=400)

    return JsonResponse({
        'ok': True,
        'id': m.id,
        'producto': producto.nombre,
        'producto_id': producto.id,
        'tipo': tipo,
        'cantidad': cantidad,
        'fecha': m.fecha.strftime('%d/%m/%Y %H:%M'),
        'stock_actual': producto.stock,
        'imagen_url': producto.imagen.url if producto.imagen else ''
    })


def informe_inventario_data(request):
    """API que devuelve los datos del inventario en formato JSON"""
    productos = Producto.objects.filter(activo=True).order_by('stock')

    productos_bajo = productos.filter(stock__lt=F('stock_minimo'))

    total_productos = productos.count()
    valor_total = productos.aggregate(total=Sum(F('stock') * F('costo')))['total'] or 0

    data = {
        'productos_bajo': [
            {
                'id': p.id,
                'nombre': p.nombre,
                'codigo_barras': p.codigo_barras,
                'stock': p.stock,
                'stock_minimo': p.stock_minimo or 5,
                'categoria': p.categoria.nombre if p.categoria else 'Sin categoría',
                'precio': float(p.precio),
            }
            for p in productos_bajo
        ],
        'productos_todos': [
            {
                'id': p.id,
                'nombre': p.nombre,
                'codigo_barras': p.codigo_barras,
                'stock': p.stock,
                'stock_minimo': p.stock_minimo or 5,
                'categoria': p.categoria.nombre if p.categoria else 'Sin categoría',
                'precio': float(p.precio),
            }
            for p in productos
        ],
        'total_productos': total_productos,
        'valor_total': round(float(valor_total), 2),
    }

    return JsonResponse(data)


from django.template.loader import render_to_string
from django.http import HttpResponse
from weasyprint import HTML
from django.db.models import F, Sum, Q
from django.utils import timezone


def informe_inventario_pdf(request):
    """Genera un PDF con el informe de inventario"""
    productos = Producto.objects.filter(activo=True).order_by('stock')
    productos_bajo = productos.filter(stock__lt=F('stock_minimo'))

    total_productos = productos.count()
    valor_total = productos.aggregate(total=Sum(F('stock') * F('costo')))['total'] or 0

    # Calcular total por producto para la tabla
    productos_con_total = []
    for p in productos:
        productos_con_total.append({
            'id': p.id,
            'codigo_barras': p.codigo_barras,
            'nombre': p.nombre,
            'categoria': p.categoria,
            'stock': p.stock,
            'precio': p.precio,
            'stock_minimo': p.stock_minimo,
            'total': p.stock * p.precio
        })

    html_string = render_to_string('stock/informe_inventario_pdf.html', {
        'productos': productos_con_total,
        'productos_bajo': productos_bajo,
        'total_productos': total_productos,
        'valor_total': valor_total,
        'fecha': timezone.now(),
    })

    html = HTML(string=html_string)
    pdf = html.write_pdf()

    response = HttpResponse(pdf, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="inventario_{timezone.now().strftime("%Y%m%d_%H%M")}.pdf"'
    return response