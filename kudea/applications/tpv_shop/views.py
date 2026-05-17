# views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from django.views.generic import TemplateView, ListView, DetailView, FormView, UpdateView, CreateView, DeleteView
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import transaction
from django.core.mail import send_mail
from django.conf import settings
from .models import Cart, CartItem, Service, Ticket, TicketItem, CajaArqueo
 # ✅ Correcto
from applications.product.models import Categoria, Producto
from .forms import EmailForm, UpdateCartItemForm, CajaArqueoForm

from decimal import Decimal
from django.db.models import Q
from datetime import datetime
from django.http import JsonResponse
from django.urls import reverse_lazy
from django.utils import timezone


from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.db.models import Sum
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.views.decorators.http import require_POST
import json


# --- Vistas de Catálogo ---
class TpvShopIndexView(TemplateView):
    template_name = 'tpv_shop/index.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['featured_products'] = Producto.objects.filter(activo=True)[:4]
        context['categories'] = Categoria.objects.all()[:6]
        return context


class ProductListView(ListView):
    model = Producto
    template_name = 'tpv_shop/product_list.html'
    context_object_name = 'products'
    paginate_by = 12

    def get_queryset(self):
        queryset = Producto.objects.filter(is_active=True)
        category_slug = self.kwargs.get('category_slug')
        if category_slug:
            queryset = queryset.filter(category__slug=category_slug)
        return queryset.select_related('category')

class ProductDetailView(DetailView):
    model = Producto
    template_name = 'tpv_shop/product_detail.html'
    context_object_name = 'product'
    slug_url_kwarg = 'slug'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Usar correctamente 'categoria' en lugar de 'category'
        context['related_products'] = Producto.objects.filter(
            categoria=self.object.categoria,
            activo=True  # si tu modelo usa 'activo' en lugar de 'is_active'
        ).exclude(id=self.object.id)[:4]

        # Información del carrito si el usuario está autenticado
        if self.request.user.is_authenticated:
            cart, _ = Cart.objects.get_or_create(user=self.request.user)
            context['cart_item_count'] = cart.items.count()
            
        return context



# --- Vistas de Categorías ---
class CategoryListView(ListView):
    model = Categoria
    template_name = 'tpv_shop/category_list.html'
    context_object_name = 'categories'
    
    def get_queryset(self):
        return Categoria.objects.prefetch_related('products')



class CategoryDetailView(DetailView):
    model = Categoria
    template_name = 'tpv_shop/category_detail.html'
    context_object_name = 'category'
    slug_url_kwarg = 'slug'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['products'] = self.object.products.filter(activo=True)
        return context



# --- Vistas de Servicios ---
class ServiceListView(ListView):
    model = Service
    template_name = 'tpv_shop/service_list.html'
    context_object_name = 'services'



class ServiceDetailView(DetailView):
    model = Service
    template_name = 'tpv_shop/service_detail.html'
    context_object_name = 'service'
    slug_url_kwarg = 'slug'



# --- Sistema de Carrito Mejorado ---
class CartBaseView(LoginRequiredMixin):
    def get_cart(self, user):
        return Cart.objects.get_or_create(user=user)[0]

    def calculate_totals(self, items):
        subtotal = sum(item.get_total_price for item in items)
        discount = sum((item.product.price * item.quantity) - item.get_total_price for item in items if item.product.discount > 0)
        tax_rate = Decimal('0.21')
        tax_amount = (subtotal - discount) * tax_rate
        total = (subtotal - discount) + tax_amount

        return {
            'subtotal': subtotal,
            'discount': discount,
            'tax_rate': tax_rate,
            'tax_amount': tax_amount,
            'total': total
        }


class CartView(View):
    def get(self, request):
        if not request.user.is_authenticated:
            messages.warning(request, "Debes iniciar sesión para ver tu carrito")
            return redirect('login')
            
        cart = get_object_or_404(Cart, user=request.user)
        items = cart.items.all()

        # Aquí está la clave: precio sin descuento
        original_price = sum(item.product.precio * item.quantity for item in items)


        subtotal = sum(item.get_total_price() for item in items)
        discount = original_price - subtotal  # Diferencia entre precio original y el precio con descuentos

        tax_rate = Decimal('0.21')
        tax_amount = (subtotal) * tax_rate
        total = subtotal + tax_amount

        context = {
        'cart': cart,
        'items': items,
        'original_price': original_price,
        'subtotal': subtotal,
        'discount_amount': discount,
        'tax_amount': tax_amount,
        'tax_rate': tax_rate * 100,
        'total_price': total,
    }

        return render(request, 'tpv_shop/cart.html', context)


class AddToCartView(CartBaseView, View):
    def post(self, request, product_id):
        product = get_object_or_404(Producto, id=product_id)
        cart = self.get_cart(request.user)
        cart_item, created = CartItem.objects.get_or_create(cart=cart, product=product)

        if not created:
            cart_item.quantity += 1
        cart_item.save()

        messages.success(request, f"'{product.nombre}' añadido al carrito")
        return redirect('tpv_shop:cart')


class RemoveFromCartView(View):
    def post(self, request, item_id):
        item = get_object_or_404(CartItem, id=item_id, cart__user=request.user)
        item.delete()
        messages.success(request, "Producto eliminado del carrito")
        return redirect('tpv_shop:cart')



class UpdateCartView(CartBaseView, View):
    def post(self, request):
        import json
        data = json.loads(request.body)
        item_id = data.get('item_id')
        new_quantity = int(data.get('quantity', 1))

        item = get_object_or_404(CartItem, id=item_id, cart__user=request.user)
        delta = new_quantity - item.quantity

        if item.product.stock < delta:
            return JsonResponse({'error': 'Stock insuficiente'}, status=400)

        item.quantity = new_quantity
        item.save()

        cart = item.cart
        subtotal = cart.get_subtotal()
        discount = cart.get_total_discount()
        tax = cart.get_tax_amount()
        total = cart.get_total_price()
        original_price = item.product.price

        return JsonResponse({
            'item_total_price': f"{item.get_total_price():.2f}",
            'original_price': f"{original_price:.2f}",
            'subtotal': f"{subtotal:.2f}",
            'discount_amount': f"{discount:.2f}",
            'tax_amount': f"{tax:.2f}",
            'total_price': f"{total:.2f}",
        })




class CheckoutView(CartBaseView, View):
    def get(self, request):
        cart = self.get_cart(request.user)
        items = cart.items.all()

        if not items:
            messages.warning(request, "Tu carrito está vacío")
            return redirect('tpv_shop:cart')

        subtotal = sum(item.get_total_price() for item in items)
        original_price = sum(item.product.precio * item.quantity for item in items)  # ✅ corregido aquí
        discount = original_price - subtotal
        tax_rate = Decimal('0.21')
        tax_amount = subtotal * tax_rate
        total = subtotal + tax_amount

        context = {
            'cart': cart,
            'items': items,
            'subtotal': subtotal,
            'discount_amount': discount,
            'tax_amount': tax_amount,
            'tax_rate': tax_rate * 100,
            'total_price': total,
            'original_price': original_price,
        }

        return render(request, 'tpv_shop/checkout.html', context)



class FinalizarCompraView(View):
    def post(self, request):
        payment_method = request.POST.get('payment_method')
        cart = get_object_or_404(Cart, user=request.user)
        items = cart.items.all()

        if not items.exists():
            messages.error(request, "El carrito está vacío.")
            return redirect('tpv_shop:cart')

        # Cálculo de totales usando campos en español
        subtotal = sum(item.get_total_price() for item in items)
        discount = sum(
            (item.product.precio * item.quantity) - item.get_total_price()
            for item in items if item.product.descuento > 0
        )
        tax_rate = Decimal('0.21')
        tax_amount = (subtotal - discount) * tax_rate
        total = (subtotal - discount) + tax_amount

        # Crear el ticket
        ticket = Ticket.objects.create(
            total=total,
            payment_method=payment_method,
            closed=True
        )

        for item in items:
            TicketItem.objects.create(
                ticket=ticket,
                product_name=item.product.nombre,
                quantity=item.quantity,
                price=item.product.final_price(),
                discount=item.product.descuento
            )

        cart.items.all().delete()
        return redirect('tpv_shop:ticket_detalle', pk=ticket.pk)


class UpdateCartAjaxView(CartBaseView, View):
    def post(self, request):
        item_id = request.POST.get('item_id')
        quantity = int(request.POST.get('quantity', 1))
        item = get_object_or_404(CartItem, id=item_id, cart__user=request.user)

        if item.product.stock < (quantity - item.quantity):
            return JsonResponse({'error': 'Stock insuficiente'}, status=400)

        item.quantity = quantity
        item.save()

        cart = self.get_cart(request.user)
        items = cart.items.all()
        totals = self.calculate_totals(items)

        return JsonResponse({
        'success': True,
        'subtotal': f"{totals['subtotal']:.2f}",
        'discount': f"{totals['discount']:.2f}",
        'tax': f"{totals['tax_amount']:.2f}",
        'total': f"{totals['total']:.2f}",
        'item_id': item.id,
        'item_total_price': f"{item.get_total_price:.2f}",  # Si es método, pon get_total_price()
    })



class ReceiptSelectionView(FormView):
    template_name = 'tpv_shop/receipt_selection.html'
    form_class = EmailForm

    def form_valid(self, form):
        email = form.cleaned_data['email']
        send_mail(
            'Tu recibo de compra',
            'Aquí está tu recibo adjunto',
            settings.DEFAULT_FROM_EMAIL,
            [email],
            fail_silently=False,
        )
        return render(self.request, 'tpv_shop/receipt_sent.html', {'email': email})


# --- Vista de Email (para recibos) ---
class EmailFormView(FormView):
    template_name = 'tpv_shop/email_form.html'
    form_class = EmailForm
    success_url = '/receipt/sent/'


class TicketListView(ListView):
    model = Ticket
    template_name = 'tpv_shop/ticket_list.html'
    context_object_name = 'tickets'
    ordering = ['-date']

    def get_queryset(self):
        queryset = super().get_queryset()
        query = self.request.GET.get('q')

        if query:
            try:
                # Buscar por fecha en formato dd/mm/yyyy
                search_date = datetime.strptime(query, '%d/%m/%Y').date()
                queryset = queryset.filter(date__date=search_date)
            except ValueError:
                # Si no es fecha, busca por ticket_number o método de pago
                queryset = queryset.filter(
                    Q(ticket_number__icontains=query) |
                    Q(payment_method__icontains=query)
                )
        return queryset



class TicketDetailView(DetailView):
    model = Ticket
    template_name = 'tpv_shop/ticket_detail.html'
    context_object_name = 'ticket'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        ticket = self.get_object()

        subtotal = Decimal(0)
        iva = Decimal(0)
        original_price = Decimal(0)

        for item in ticket.items.all():
            item_total = item.get_subtotal()  # ya es cantidad * precio con descuento
            subtotal += item_total
            iva += item_total * Decimal('0.21')
            original_price += item.quantity * (item.price / (1 - item.discount / 100)) if item.discount else item.get_subtotal()

        total = subtotal + iva

        context['subtotal'] = round(subtotal, 2)
        context['iva'] = round(iva, 2)
        context['total'] = round(total, 2)
        context['original_price'] = round(original_price, 2)

        return context



class EliminarTicketView(View):
    def post(self, request, pk):
        ticket = get_object_or_404(Ticket, pk=pk)
        ticket.delete()
        return redirect('tpv_shop:ticket_list')




def tickets_del_dia(request):
    fecha = timezone.now().date()
    inicio = timezone.make_aware(datetime.combine(fecha, time.min))
    fin = timezone.make_aware(datetime.combine(fecha, time.max))

    tickets = Ticket.objects.filter(
        date__range=(inicio, fin),
        is_returned=False,
        closed=True
    )

    print("Tickets encontrados:", tickets)  # 👈 MUY IMPORTANTE: para ver en consola

    data = {
        'tickets': [
            {
                'ticket_number': t.ticket_number,
                'payment_method': t.payment_method,
                'total': str(t.total),
            } for t in tickets
        ]
    }
    return JsonResponse(data)




class CajaArqueoCreateView(CreateView):
    model = CajaArqueo
    form_class = CajaArqueoForm
    template_name = "tpv_shop/arqueo_caja.html"
    success_url = reverse_lazy("tpv_shop:caja_arqueo_list")

    def form_valid(self, form):
        arqueo = form.save(commit=False)
        arqueo.usuario = self.request.user
        arqueo.total_ventas = self.calcular_total_ventas_del_dia()
        arqueo.save()
        return super().form_valid(form)

    def calcular_total_ventas_del_dia(self):
        today = timezone.now().date()
        tickets = Ticket.objects.filter(date__isnull=False, date__date=today)
        return sum(ticket.total for ticket in tickets)


class CajaArqueoListView(View):
    def get(self, request, *args, **kwargs):
        arqueos = CajaArqueo.objects.all().order_by('-fecha')
        return render(request, 'tpv_shop/caja_arqueo_list.html', {'arqueos': arqueos})



class CajaArqueoDetailView(DetailView):
    model = CajaArqueo
    template_name = 'tpv_shop/caja_arqueo_detail.html'
    context_object_name = 'arqueo'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        arqueo = self.get_object()

        # Obteniendo los tickets relacionados al arqueo
        tickets = Ticket.objects.filter(date__date=arqueo.fecha.date())
        items = []

        # Acumulando datos de cada ticket
        total_subtotal = Decimal('0.00')
        total_discount = Decimal('0.00')
        total_tax = Decimal('0.00')
        total_price = Decimal('0.00')

        for ticket in tickets:
            for item in ticket.items.all():
                # Obtener precio original y precio con descuento
                price_original = item.original_price  # Directo del campo original_price
                price_with_discount = item.price
                subtotal = price_with_discount * item.quantity
                discount = price_original - price_with_discount
                tax = subtotal * Decimal('0.21')  # Suponiendo un IVA del 21%
                subtotal_with_tax = subtotal + tax

                total_subtotal += subtotal
                total_discount += discount
                total_tax += tax
                total_price += subtotal_with_tax

                # Pasando datos a la plantilla
                items.append({
                    'product_name': item.product_name,
                    'ticket_number': ticket.ticket_number,
                    'quantity': item.quantity,
                    'price_with_discount': price_with_discount,
                    'price_original': price_original,
                    'subtotal_with_tax': subtotal_with_tax
                })

        context.update({
            'ticket_items': items,
            'subtotal': total_subtotal,
            'discount_amount': total_discount,
            'tax_amount': total_tax,
            'total_price': total_price,
            'tax_rate': 21,  # Suponiendo un 21% de IVA
        })

        return context





class CajaArqueoDeleteView(DeleteView):
    model = CajaArqueo
    success_url = reverse_lazy('tpv_shop:caja_arqueo_list')  # Ajusta si tu lista se llama distinto
    template_name = 'tpv_shop/caja_arqueo_confirm_delete.html'




class ArqueoAutomaticoView(View):
    def get(self, request, *args, **kwargs):
        fecha_actual = timezone.now().date()
        return render(request, 'tpv_shop/arqueo_auto.html', {'fecha_actual': fecha_actual})

    def post(self, request, *args, **kwargs):
        hoy = timezone.now().date()
        
        try:
            efectivo_inicial = Decimal(request.POST.get('efectivo_inicial', 0))
        except (ValueError, TypeError):
            return JsonResponse({'error': 'Efectivo inicial no válido'}, status=400)

        # Obtener todos los tickets generados hoy (no devueltos)
        tickets = Ticket.objects.filter(date__date=hoy, is_returned=False, closed=True)

        # Inicialización de variables
        total_efectivo = total_tarjeta = total_bizum = total_ventas = total_articulos = Decimal('0.00')

        # Sumar los totales de las ventas
        for ticket in tickets:
            total_efectivo += ticket.total if ticket.payment_method == 'efectivo' else Decimal('0.00')
            total_tarjeta += ticket.total if ticket.payment_method == 'tarjeta' else Decimal('0.00')
            total_bizum += ticket.total if ticket.payment_method == 'bizum' else Decimal('0.00')
            total_ventas += ticket.total

            # Sumar el total de artículos vendidos
            total_articulos += ticket.items.aggregate(Sum('quantity'))['quantity__sum'] or 0

        # Calcular la diferencia entre efectivo final e inicial
        diferencia = total_efectivo - efectivo_inicial

        # Crear el arqueo (pero no guardarlo todavía)
        arqueo_data = {
            'efectivo_inicial': float(efectivo_inicial),
            'efectivo_final': float(total_efectivo),
            'tarjeta_total': float(total_tarjeta),
            'bizum_total': float(total_bizum),
            'total_ventas': float(total_ventas),
            'total_articulos_vendidos': int(total_articulos),
            'diferencia': float(diferencia),
        }

        return JsonResponse(arqueo_data)




@require_POST
@csrf_exempt
def guardar_arqueo_auto(request):
    try:
        data = json.loads(request.body)
        arqueo = CajaArqueo.objects.create(
            usuario=request.user,
            efectivo_inicial=Decimal(data.get('efectivo_inicial', 0)),
            efectivo_final=Decimal(data.get('efectivo_final', 0)),
            tarjeta_total=Decimal(data.get('tarjeta_total', 0)),
            bizum_total=Decimal(data.get('bizum_total', 0)),
            total_ventas=Decimal(data.get('total_ventas', 0)),
            total_articulos_vendidos=int(data.get('total_articulos_vendidos', 0)),
            observaciones="Guardado desde vista automática"
        )
        return JsonResponse({'status': 'ok', 'redirect_url': f'/arqueos/{arqueo.pk}/'})
    except Exception as e:
        print("Error al guardar arqueo:", e)
        return JsonResponse({'error': 'Error al guardar arqueo'}, status=400)
