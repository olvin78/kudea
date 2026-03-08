from django.db import models
from django.utils.translation import gettext_lazy as _
from django.conf import settings
from django.utils.text import slugify
from django.contrib.auth.models import User
from decimal import Decimal
from django import forms


class Category(models.Model):
    name = models.CharField(max_length=255)
    slug = models.SlugField(unique=True, blank=True)
    icon = models.ImageField(upload_to='categories/', blank=True, null=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class Product(models.Model):
    class ProductType(models.TextChoices):
        PHYSICAL = 'physical', _('Physical')
        DIGITAL = 'digital', _('Digital')

    name = models.CharField(max_length=255)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    discount = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    category = models.ForeignKey(Category, related_name='products', on_delete=models.CASCADE)
    image = models.ImageField(upload_to='products/', null=True, blank=True)
    stock = models.PositiveIntegerField(default=0, null=True, blank=True)
    is_active = models.BooleanField(default=True)
    slug = models.SlugField(unique=True)
    product_type = models.CharField(max_length=10, choices=ProductType.choices, default=ProductType.PHYSICAL)
    weight = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    size = models.CharField(max_length=50, blank=True, null=True)
    color = models.CharField(max_length=50, blank=True, null=True)
    file = models.FileField(upload_to='digital_products/', null=True, blank=True)

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return f"/producto/{self.slug}/"

    def is_in_stock(self):
        return self.stock > 0

    def decrease_stock(self, quantity=1):
        if self.is_in_stock():
            self.stock -= quantity
            self.save()

    def final_price(self):
        return self.price * (1 - self.discount / 100)


class Service(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    category = models.ForeignKey(Category, related_name='services', on_delete=models.CASCADE)
    is_active = models.BooleanField(default=True)
    duration = models.PositiveIntegerField(help_text="Duración en minutos")
    slug = models.SlugField(unique=True)

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return f"/servicio/{self.slug}/"


class Cart(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    def get_subtotal(self):
        return sum(item.get_total_price() for item in self.items.select_related('product'))

    def get_total_discount(self):
        return sum(
            (item.product.price * item.quantity) - item.get_total_price()
            for item in self.items.select_related('product')
            if item.product.discount > 0
        )

    def get_tax_amount(self):
        subtotal = self.get_subtotal()
        return subtotal * Decimal('0.21')

    def get_total_price(self):
        return self.get_subtotal() + self.get_tax_amount()

    def __str__(self):
        return f"Carrito de {self.user.username}"


class CartItem(models.Model):
    cart = models.ForeignKey(Cart, related_name='items', on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)

    def get_total_price(self):
        return self.product.final_price() * self.quantity


    def get_original_price(self):
        return self.product.price * self.quantity

    def __str__(self):
        return f"{self.quantity} x {self.product.name}"


class Ticket(models.Model):
    ticket_number = models.CharField(max_length=10, unique=True, blank=True, null=True)
    date = models.DateTimeField(auto_now_add=True)
    total = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    payment_method = models.CharField(
        max_length=20,
        choices=[('efectivo', 'Efectivo'), ('tarjeta', 'Tarjeta'), ('bizum', 'Bizum')]
    )
    closed = models.BooleanField(default=False)
    is_returned = models.BooleanField(default=False)  # Agregado el campo is_returned

    def save(self, *args, **kwargs):
        if not self.ticket_number:
            last = Ticket.objects.all().order_by('id').last()
            next_id = last.id + 1 if last else 1
            self.ticket_number = f'TK{next_id:05d}'
        super().save(*args, **kwargs)

    def __str__(self):
        return self.ticket_number or f'Ticket #{self.id}'


class TicketItem(models.Model):
    ticket = models.ForeignKey(Ticket, related_name='items', on_delete=models.CASCADE)
    product_name = models.CharField(max_length=100, blank=True, null=True)
    quantity = models.PositiveIntegerField(blank=True, null=True)
    discount = models.DecimalField(max_digits=5, decimal_places=2, default=0, blank=True, null=True)
    price = models.DecimalField(max_digits=8, decimal_places=2, blank=True, null=True)

    @property
    def original_price(self):
        if self.discount and self.discount > 0:
            return self.price / (1 - (self.discount / 100))
        return self.price


    def total(self):
        if self.quantity and self.price:
            return self.quantity * self.price
        return Decimal(0)

    def get_subtotal(self):
        return self.quantity * self.price if self.quantity and self.price else Decimal(0)


class Invoice(models.Model):
    ticket = models.OneToOneField(Ticket, on_delete=models.CASCADE, blank=True, null=True)
    client_name = models.CharField(max_length=100, blank=True, null=True)
    client_nif = models.CharField(max_length=20, blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    issued_date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Factura #{self.pk} para {self.client_name or 'Cliente'}"



class CajaArqueo(models.Model):
    fecha = models.DateTimeField(auto_now_add=True)
    usuario = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    
    efectivo_inicial = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    efectivo_final = models.DecimalField(max_digits=10, decimal_places=2)
    tarjeta_total = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    bizum_total = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    total_ventas = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    total_articulos_vendidos = models.PositiveIntegerField(default=0)  # Asegúrate de tener este campo en tu modelo
    
    observaciones = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"Arqueo del {self.fecha.strftime('%d/%m/%Y')} - {self.usuario}"

    def calcular_total_ventas(self):
        from .models import Ticket, TicketItem  # <-- importación local

        if self.fecha:
            tickets = Ticket.objects.filter(date__date=self.fecha.date(), is_returned=False)  # Filtra por fecha y no devueltos
        else:
            tickets = []

        total_efectivo = total_tarjeta = total_bizum = total_ventas = total_articulos = Decimal('0.00')

        for ticket in tickets:
            total_efectivo += ticket.total if ticket.payment_method == 'efectivo' else Decimal('0.00')
            total_tarjeta += ticket.total if ticket.payment_method == 'tarjeta' else Decimal('0.00')
            total_bizum += ticket.total if ticket.payment_method == 'bizum' else Decimal('0.00')
            total_ventas += ticket.total

            # Calcular el total de artículos vendidos
            total_articulos += ticket.items.aggregate(Sum('quantity'))['quantity__sum'] or 0

        self.total_ventas = total_ventas
        self.efectivo_final = total_efectivo
        self.tarjeta_total = total_tarjeta
        self.bizum_total = total_bizum
        self.total_articulos_vendidos = total_articulos

        self.save()

