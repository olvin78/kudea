import uuid
import random
import string
from django.db import models
from applications.product.models import Producto  # Ajusta si tu ruta es distinta

from applications.home.models import Venta, DetalleVenta, MetodoPago
from applications.product.models import Producto

def crear_venta(request):
    # Lógica para crear la venta
    venta = Venta.objects.create(
        usuario=request.user,
        metodo_pago=MetodoPago.objects.first(),  # ejemplo
        subtotal=50.00,
        iva=10.00,
        total=60.00,
        recibido=60.00,
        cambio=0.00,
        estado='completada',
    )

    DetalleVenta.objects.create(
        venta=venta,
        producto=Producto.objects.first(),
        cantidad=2,
        precio_unitario=25.00,
        total=50.00
    )



class Mesa(models.Model):
    ESTADO_CHOICES = [
        ('libre', 'Libre'),
        ('ocupada', 'Ocupada'),
        ('reservada', 'Reservada'),
        ('esperando', 'Esperando pedido'),
    ]

    nombre = models.CharField(max_length=100, unique=True)
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='libre')
    capacidad = models.PositiveIntegerField(default=4)
    creada = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Mesa {self.nombre} ({self.get_estado_display()})"

    def tiene_comanda_abierta(self):
        return self.comandas.filter(estado='abierta').exists()

    def comanda_abierta(self):
        return self.comandas.filter(estado='abierta').first()


class Comanda(models.Model):
    ESTADO_CHOICES = [
        ('abierta', 'Abierta'),
        ('servida', 'Servida'),
        ('cerrada', 'Cerrada'),
    ]

    mesa = models.ForeignKey(Mesa, on_delete=models.CASCADE, related_name='comandas')
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='abierta')
    total = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)

    def __str__(self):
        return f"Comanda {self.id} - Mesa {self.mesa.nombre}"

    def calcular_total(self):
        total = sum(item.subtotal() for item in self.items.all())
        self.total = total
        self.save()
        return total


class ComandaItem(models.Model):
    comanda = models.ForeignKey(Comanda, on_delete=models.CASCADE, related_name='items')
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE)
    cantidad = models.PositiveIntegerField(default=1)
    precio_unitario = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)

    def subtotal(self):
        return self.cantidad * self.precio_unitario

    def __str__(self):
        return f"{self.cantidad}x {self.producto.nombre} (Comanda {self.comanda.id})"


class Ticket(models.Model):
    ESTADO_CHOICES = [
        ('pendiente', 'Pendiente'),
        ('pagado', 'Pagado'),
        ('cancelado', 'Cancelado'),
    ]

    comanda = models.ForeignKey(Comanda, on_delete=models.CASCADE, related_name='tickets')
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='pendiente')
    total = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)

    def __str__(self):
        return f"Ticket #{self.id} - Comanda {self.comanda.id}"

    def calcular_total(self):
        self.total = sum(item.subtotal() for item in self.comanda.items.all())
        self.save()
        return self.total


def generar_codigo_aleatorio(longitud=4):
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=longitud))


class Empleado(models.Model):
    nombre = models.CharField(max_length=100)
    apellidos = models.CharField(max_length=100, blank=True, null=True)
    nif = models.CharField(max_length=15, blank=True, null=True)
    usuario = models.CharField(max_length=50, blank=True, null=True)
    email = models.EmailField()
    telefono = models.CharField(max_length=15, blank=True, null=True)
    movil = models.CharField(max_length=15, blank=True, null=True)
    direccion = models.CharField(max_length=255, blank=True, null=True)
    cp = models.CharField(max_length=10, blank=True, null=True)
    poblacion = models.CharField(max_length=100, blank=True, null=True)
    provincia = models.CharField(max_length=100, blank=True, null=True)

    codigo = models.CharField(max_length=50, blank=True, editable=False)

    # Permisos
    es_administrador = models.BooleanField(default=False)
    puede_realizar_salidas = models.BooleanField(default=False)
    puede_cambiar_fecha_hora = models.BooleanField(default=False)
    puede_modificar_ventas = models.BooleanField(default=False)
    puede_cambiar_subtotales = models.BooleanField(default=False)
    puede_cambiar_tarifa = models.BooleanField(default=False)

    esta_de_baja = models.BooleanField(default=False)
    fecha_baja = models.DateField(blank=True, null=True)
    observaciones = models.TextField(blank=True, null=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    ultima_modificacion = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.nombre

    def save(self, *args, **kwargs):
        if not self.codigo:
            iniciales = ''.join([x[0] for x in self.nombre.strip().split()[:2] if x]).upper()
            if not iniciales:
                iniciales = 'EMP'
            usuario_part = (self.usuario or '').strip().upper() or generar_codigo_aleatorio(2)
            aleatorio = generar_codigo_aleatorio(3)
            self.codigo = f"{iniciales}-{usuario_part}{aleatorio}"
        super().save(*args, **kwargs)

