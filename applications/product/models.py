
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils.text import slugify
from decimal import Decimal
import random
import string

class Categoria(models.Model):
    nombre = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=100, unique=True, blank=True)
    icono = models.ImageField(upload_to='categorias/', blank=True, null=True)
    descripcion = models.TextField(blank=True, null=True)
    creado_en = models.DateTimeField(auto_now_add=True)
    actualizado_en = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Categoría"
        verbose_name_plural = "Categorías"
        ordering = ['nombre']

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.nombre)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.nombre





class Producto(models.Model):
    class TipoProducto(models.TextChoices):
        FISICO = 'fisico', 'Físico'
        DIGITAL = 'digital', 'Digital'

    VALORES_IVA = [
        (Decimal('21.00'), '21%'),
        (Decimal('15.00'), '15%'),
        (Decimal('10.00'), '10%'),
        (Decimal('4.00'), '4%'),
        (Decimal('0.00'), '0% (Exento)'),
    ]

    codigo_barras = models.CharField(max_length=50, unique=True, blank=True, null=True)
    nombre = models.CharField(max_length=200)
    slug = models.SlugField(unique=True, blank=True, null=True)
    categoria = models.ForeignKey('Categoria', on_delete=models.SET_NULL, null=True, blank=True, related_name='products')
    precio = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    porcentaje_iva = models.DecimalField(max_digits=5, decimal_places=2, choices=VALORES_IVA, default=Decimal('21.00'))
    costo = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)], blank=True, null=True)
    descuento = models.DecimalField(max_digits=5, decimal_places=2, default=0, validators=[MinValueValidator(0), MaxValueValidator(100)])
    stock = models.IntegerField(default=0, validators=[MinValueValidator(0)])
    stock_minimo = models.IntegerField(default=5, validators=[MinValueValidator(0)])
    activo = models.BooleanField(default=True)
    imagen = models.ImageField(upload_to='productos/', blank=True, null=True)
    tipo_producto = models.CharField(max_length=10, choices=TipoProducto.choices, default=TipoProducto.FISICO)
    peso = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)
    talla = models.CharField(max_length=50, blank=True, null=True)
    color = models.CharField(max_length=50, blank=True, null=True)
    archivo = models.FileField(upload_to='productos_digitales/', blank=True, null=True)
    creado_en = models.DateTimeField(auto_now_add=True)
    actualizado_en = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Producto"
        verbose_name_plural = "Productos"
        ordering = ['nombre']

    def __str__(self):
        return f"{self.nombre} - {self.precio}€"

    @property
    def necesita_reposicion(self):
        return self.stock < self.stock_minimo

    def final_price(self):
        return self.precio * (1 - self.descuento / Decimal(100))

    def is_in_stock(self):
        return self.stock > 0

    def decrease_stock(self, quantity=1):
        if self.is_in_stock() and self.stock >= quantity:
            self.stock -= quantity
            self.save()

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.nombre)
            slug = base_slug
            counter = 1
            while Producto.objects.filter(slug=slug).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            self.slug = slug

        if not self.codigo_barras:
            # Generate a 12-digit random numeric code as default (like EAN-13 but simpler)
            while True:
                new_code = 'KUD-' + ''.join(random.choices(string.digits, k=8))
                if not Producto.objects.filter(codigo_barras=new_code).exists():
                    self.codigo_barras = new_code
                    break

        super().save(*args, **kwargs)