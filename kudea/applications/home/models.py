from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator
from django.core.exceptions import ValidationError

from applications.config.models import ConfiguracionFiscal

# Importa Producto desde la app nueva
from applications.product.models import Producto, Categoria
from applications.payments.models import MetodoPago

class Modulo(models.Model):
    nombre = models.CharField(max_length=100, unique=True)
    clave = models.CharField(max_length=100, unique=True)
    activo = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Módulo"
        verbose_name_plural = "Módulos"

    def __str__(self):
        return f"{self.nombre} ({'Activo' if self.activo else 'Inactivo'})"



"""

class MetodoPago(models.Model):
    nombre = models.CharField(max_length=50, unique=True)
    descripcion = models.TextField(blank=True, null=True)
    imagen = models.ImageField(upload_to='metodos_pago/', blank=True, null=True)
    activo = models.BooleanField(default=True)
    acepta_cambio = models.BooleanField(default=False)

    class Meta:
        verbose_name = "Método de pago"
        verbose_name_plural = "Métodos de pago"
        ordering = ['nombre']

    def __str__(self):
        return self.nombre

"""

class Venta(models.Model):
    ESTADOS = (
        ('pendiente', 'Pendiente'),
        ('completada', 'Completada'),
        ('cancelada', 'Cancelada'),
    )

    codigo = models.CharField(max_length=20, unique=True)
    usuario = models.ForeignKey(User, on_delete=models.PROTECT)
    metodo_pago = models.ForeignKey(MetodoPago, on_delete=models.PROTECT)
    subtotal = models.DecimalField(max_digits=10, decimal_places=2)
    iva = models.DecimalField(max_digits=10, decimal_places=2)
    total = models.DecimalField(max_digits=10, decimal_places=2)
    descuento = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    recibido = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    cambio = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    estado = models.CharField(max_length=20, choices=ESTADOS, default='completada')
    notas = models.TextField(blank=True, null=True)
    creado_en = models.DateTimeField(auto_now_add=True)
    actualizado_en = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Venta"
        verbose_name_plural = "Ventas"
        ordering = ['-creado_en']

    def __str__(self):
        return f"Venta #{self.codigo} - {self.total}€"

    def save(self, *args, **kwargs):
        if not self.codigo:
            last_venta = Venta.objects.order_by('-id').first()
            last_id = last_venta.id if last_venta else 0
            self.codigo = f"VT-{last_id + 1:06d}"
        super().save(*args, **kwargs)


class DetalleVenta(models.Model):
    venta = models.ForeignKey(Venta, related_name='detalles', on_delete=models.CASCADE)
    producto = models.ForeignKey(Producto, on_delete=models.PROTECT)
    cantidad = models.IntegerField(validators=[MinValueValidator(1)])
    precio_unitario = models.DecimalField(max_digits=10, decimal_places=2)
    total = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        verbose_name = "Detalle de venta"
        verbose_name_plural = "Detalles de venta"

    def __str__(self):
        return f"{self.cantidad}x {self.producto.nombre} - {self.total}€"


class ConfiguracionTPV(models.Model):
    nombre_tienda = models.CharField(max_length=100, default="Mi Tienda")
    logo = models.ImageField(upload_to='config/', blank=True, null=True)
    iva_por_defecto = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=15,
        validators=[MinValueValidator(0)]
    )
    moneda = models.CharField(max_length=10, default="€")
    imprimir_tickets = models.BooleanField(default=True)
    mostrar_stock = models.BooleanField(default=True)
    pin_apertura = models.CharField(max_length=4, default="1234", verbose_name="PIN de apertura de caja")
    actualizado_en = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Configuración TPV"
        verbose_name_plural = "Configuraciones TPV"

    def __str__(self):
        return f"Configuración de {self.nombre_tienda}"

    def save(self, *args, **kwargs):
        if not self.pk and ConfiguracionTPV.objects.exists():
            raise ValidationError("Solo puede existir una configuración del TPV")
        super().save(*args, **kwargs)


class CajaArqueo(models.Model):
    usuario = models.ForeignKey(User, on_delete=models.PROTECT, related_name='arqueos')
    efectivo_inicial = models.DecimalField(max_digits=10, decimal_places=2)
    efectivo_final = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    total_ventas = models.DecimalField(max_digits=10, decimal_places=2)
    diferencia = models.DecimalField(max_digits=10, decimal_places=2)
    creado_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Arqueo de Caja"
        verbose_name_plural = "Arqueos de Caja"
        ordering = ['-creado_en']

    def __str__(self):
        return f"Arqueo #{self.id} - {self.creado_en.strftime('%d/%m/%Y')}"


class Comunicacion(models.Model):
    emisor = models.ForeignKey(User, on_delete=models.CASCADE, related_name='comunicaciones_enviadas')
    titulo = models.CharField(max_length=200)
    contenido = models.TextField()
    creado_en = models.DateTimeField(auto_now_add=True)
    visto_por = models.ManyToManyField(User, related_name='comunicaciones_vistas', blank=True)

    class Meta:
        verbose_name = "Comunicación"
        verbose_name_plural = "Comunicaciones"
        ordering = ['-creado_en']

    def __str__(self):
        return self.titulo
