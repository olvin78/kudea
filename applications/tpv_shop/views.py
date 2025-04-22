# views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from django.views.generic import TemplateView, ListView, DetailView, FormView
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import transaction
from django.core.mail import send_mail
from django.conf import settings

from .models import Product, Category, Cart, CartItem, Service, Ticket, TicketItem
from .forms import EmailForm, UpdateCartItemForm

from decimal import Decimal
from django.db.models import Q
from datetime import datetime


# --- Vistas de Catálogo ---
class TpvShopIndexView(TemplateView):
    template_name = 'tpv_shop/index.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['featured_products'] = Product.objects.filter(is_active=True)[:4]
        context['categories'] = Category.objects.all()[:6]
        return context


class ProductListView(ListView):
    model = Product
    template_name = 'tpv_shop/product_list.html'
    context_object_name = 'products'
    paginate_by = 12

    def get_queryset(self):
        queryset = Product.objects.filter(is_active=True)
        category_slug = self.kwargs.get('category_slug')
        if category_slug:
            queryset = queryset.filter(category__slug=category_slug)
        return queryset.select_related('category')

class ProductDetailView(DetailView):
    model = Product
    template_name = 'tpv_shop/product_detail.html'
    context_object_name = 'product'
    slug_url_kwarg = 'slug'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['related_products'] = Product.objects.filter(
            category=self.object.category,
            is_active=True
        ).exclude(id=self.object.id)[:4]
        
        # Añadir información del carrito si el usuario está autenticado
        if self.request.user.is_authenticated:
            cart, _ = Cart.objects.get_or_create(user=self.request.user)
            context['cart_item_count'] = cart.items.count()
            
        return context


# --- Vistas de Categorías ---
class CategoryListView(ListView):
    model = Category
    template_name = 'tpv_shop/category_list.html'
    context_object_name = 'categories'
    
    def get_queryset(self):
        return Category.objects.prefetch_related('products')

class CategoryDetailView(DetailView):
    model = Category
    template_name = 'tpv_shop/category_detail.html'
    context_object_name = 'category'
    slug_url_kwarg = 'slug'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['products'] = self.object.products.filter(is_active=True)
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
    """Clase base para operaciones del carrito"""
    
    def get_cart(self, user):
        return Cart.objects.get_or_create(user=user)[0]
    
    def get_cart_items(self, cart):
        return CartItem.objects.filter(cart=cart).select_related('product')
    
    def calculate_totals(self, items):
        subtotal = sum(item.get_total_price() for item in items)
        discount = sum(
            (item.product.price * item.quantity) - item.get_total_price()
            for item in items if item.product.discount > 0
        )
        return {
            'subtotal': subtotal,
            'discount': discount,
            'total': subtotal,
            'items_count': items.count()
        }


class CartView(View):
    def get(self, request):
        if not request.user.is_authenticated:
            messages.warning(request, "Debes iniciar sesión para ver tu carrito")
            return redirect('login')
            
        cart = get_object_or_404(Cart, user=request.user)
        items = cart.items.all()
        
        # Cálculos detallados
        subtotal = sum(item.get_total_price for item in items)
        discount = sum(
            (item.product.price * item.quantity) - item.get_total_price
            for item in items if item.product.discount > 0
        )
        tax_rate = Decimal('0.21')  # 21% IVA
        tax_amount = (subtotal - discount) * tax_rate
        total = (subtotal - discount) + tax_amount
        
        context = {
            'cart': cart,
            'items': items,
            'subtotal': subtotal,
            'discount_amount': discount,
            'tax_amount': tax_amount,
            'tax_rate': tax_rate * 100,
            'total_price': total,
        }
        return render(request, 'tpv_shop/cart.html', context)

class AddToCartView(View):
    def post(self, request, product_id):
        if not request.user.is_authenticated:
            messages.warning(request, "Debes iniciar sesión para añadir productos al carrito")
            return redirect('login')
            
        product = get_object_or_404(Product, id=product_id)
        cart, _ = Cart.objects.get_or_create(user=request.user)
        
        cart_item, created = CartItem.objects.get_or_create(
            cart=cart,
            product=product,
            defaults={'quantity': 1}
        )
        
        if not created:
            cart_item.quantity += 1
            cart_item.save()
            
        messages.success(request, f"'{product.name}' añadido al carrito")
        return redirect('tpv_shop:category_list')  # ← Redirección actualizada


class RemoveFromCartView(View):
    def post(self, request, item_id):  # <- aquí añadimos item_id
        cart_item = get_object_or_404(CartItem, id=item_id, cart__user=request.user)
        cart_item.delete()
        messages.success(request, "Producto eliminado del carrito")
        return redirect('tpv_shop:cart')


class UpdateCartView(CartBaseView, View):
    def post(self, request):
        item_id = request.POST.get('item_id')
        new_quantity = int(request.POST.get('quantity', 1))
        
        with transaction.atomic():
            item = get_object_or_404(CartItem, id=item_id, cart__user=request.user)
            delta = new_quantity - item.quantity
            
            if item.product.stock < delta:
                messages.error(request, "Stock insuficiente")
                return redirect('tpv_shop:cart')
            
            item.quantity = new_quantity
            item.save()
            item.product.decrease_stock(delta)
            item.product.save()
            
        messages.success(request, "Carrito actualizado")
        return redirect('tpv_shop:cart')


class CheckoutView(CartBaseView, View):
    def get(self, request):
        cart = self.get_cart(request.user)
        items = cart.items.all()  # Usamos la relación directa del modelo Cart
        
        if not items.exists():
            messages.warning(request, "Tu carrito está vacío")
            return redirect('tpv_shop:product_list')
        
        # Cálculos detallados
        subtotal = sum(item.get_total_price for item in items)
        discount = sum(
            (item.product.price * item.quantity) - item.get_total_price 
            for item in items if item.product.discount > 0
        )
        tax_rate = Decimal('0.21')  # 21% IVA
        tax_amount = (subtotal - discount) * tax_rate
        total = (subtotal - discount) + tax_amount
        
        # Métodos de pago (simulados, reemplaza con tu modelo real)
        payment_methods = [
            {'id': 1, 'name': 'Tarjeta de crédito', 'icon': 'fas fa-credit-card'},
            {'id': 2, 'name': 'PayPal', 'icon': 'fab fa-paypal'},
            {'id': 3, 'name': 'Efectivo', 'icon': 'fas fa-money-bill-wave'},
        ]
        
        context = {
            'cart': cart,
            'items': items,
            'payment_methods': payment_methods,
            'subtotal': subtotal,
            'discount_amount': discount,
            'tax_amount': tax_amount,
            'tax_rate': tax_rate * 100,  # Para mostrar como porcentaje
            'total_price': total,
        }
        return render(request, 'tpv_shop/checkout.html', context)



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


def finalizar_compra(request):
    if request.method == "POST":
        payment_method = request.POST.get('payment_method')
        cart, _ = Cart.objects.get_or_create(user=request.user)

        if not cart.items.exists():
            messages.error(request, "El carrito está vacío.")
            return redirect('tpv_shop:cart')

        # Aquí calculamos el total correctamente sin paréntesis
        total_price = cart.get_total_price  # Llamamos a la propiedad, no con paréntesis

        # Creamos el ticket con el total calculado.
        ticket = Ticket.objects.create(
            total=total_price,  # Usamos el valor calculado correctamente
            payment_method=payment_method,
            closed=True
        )

        for item in cart.items.all():
            discounted_price = item.product.final_price()  # Aplica el descuento al precio del producto
            TicketItem.objects.create(
                ticket=ticket,
                product_name=item.product.name,
                quantity=item.quantity,
                price=discounted_price,  # Usamos el precio con descuento
                discount=item.product.discount  # Aplica el descuento
            )


        cart.items.all().delete()

        # Redirige al detalle del ticket
        return redirect('tpv_shop:ticket_detalle', pk=ticket.pk)

    return redirect('tpv_shop:checkout')


class TicketDetailView(DetailView):
    model = Ticket
    template_name = 'tpv_shop/ticket_detail.html'
    context_object_name = 'ticket'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        ticket = self.get_object()

        # Inicializamos el subtotal y el IVA
        subtotal = Decimal(0)
        iva = Decimal(0)
        
        # Calculamos el subtotal y el IVA para cada item
        for item in ticket.items.all():
            # Calculamos el precio con descuento
            discounted_price = item.price * (1 - item.discount / 100)  # Precio con descuento
            item_total = item.quantity * discounted_price
            subtotal += item_total
            iva += item_total * Decimal(0.21)  # IVA del 21%

        total = subtotal + iva

        # Agregamos los valores al contexto
        context['subtotal'] = round(subtotal, 2)
        context['iva'] = round(iva, 2)
        context['total'] = round(total, 2)

        return context

