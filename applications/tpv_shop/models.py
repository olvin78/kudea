from django.db import models
from django.utils.translation import gettext_lazy as _
from django.conf import settings
from django.utils.text import slugify
from django.contrib.auth.models import User
from decimal import Decimal





class Category(models.Model):
    name = models.CharField(max_length=255)
    slug = models.SlugField(unique=True, blank=True)
    icon = models.ImageField(upload_to='categories/', blank=True, null=True)  # Opcional, si deseas agregar iconos de imagen

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)  # Generar el slug automáticamente
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


# Modelo de Producto (Físico y Digital)
class Product(models.Model):
    class ProductType(models.TextChoices):
        PHYSICAL = 'physical', _('Physical')
        DIGITAL = 'digital', _('Digital')

    name = models.CharField(max_length=255)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    discount = models.DecimalField(max_digits=5, decimal_places=2, default=0, help_text="Descuento aplicado")
    category = models.ForeignKey(Category, related_name='products', on_delete=models.CASCADE)
    image = models.ImageField(upload_to='products/', null=True, blank=True)
    stock = models.PositiveIntegerField(default=0, null=True, blank=True)
    is_active = models.BooleanField(default=True)
    slug = models.SlugField(unique=True)
    product_type = models.CharField(max_length=10, choices=ProductType.choices, default=ProductType.PHYSICAL)
    weight = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)  # Peso del producto
    size = models.CharField(max_length=50, blank=True, null=True)  # Talla del producto (para ropa, calzado, etc.)
    color = models.CharField(max_length=50, blank=True, null=True)  # Color del producto
    file = models.FileField(upload_to='digital_products/', null=True, blank=True)  # Para productos digitales

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return f"/producto/{self.slug}/"  # URL amigable para el producto

    def is_in_stock(self):
        return self.stock > 0

    def decrease_stock(self, quantity=1):
        if self.is_in_stock():
            self.stock -= quantity
            self.save()
    
    def final_price(self):
        return self.price * (1 - self.discount / 100)  # Esto aplica el descuento correctamente



# Modelo de Servicio
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

    @property
    def get_subtotal(self):
        return sum(item.get_total_price for item in self.items.all())

    @property
    def get_total_discount(self):
        return sum(
            (item.product.price * item.quantity) - item.get_total_price
            for item in self.items.all()
            if item.product.discount > 0
        )

    @property
    def get_tax_amount(self):
        subtotal = self.get_subtotal
        return subtotal * Decimal('0.21')  # Ajusta el IVA según necesites

    @property
    def get_total_price(self):
        return self.get_subtotal + self.get_tax_amount

    def __str__(self):
        return f"Carrito de {self.user.username}"





class CartItem(models.Model):
    cart = models.ForeignKey(Cart, related_name='items', on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)

    @property
    def get_total_price(self):
        return self.product.final_price() * self.quantity

    def __str__(self):
        return f"{self.quantity} x {self.product.name}"




# models.py



class Ticket(models.Model):
    ticket_number = models.CharField(max_length=10, unique=True, blank=True, null=True)
    date = models.DateTimeField(auto_now_add=True)
    total = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    payment_method = models.CharField(
        max_length=20,
        choices=[('efectivo', 'Efectivo'), ('tarjeta', 'Tarjeta'), ('bizum', 'Bizum')]
    )
    closed = models.BooleanField(default=False)

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