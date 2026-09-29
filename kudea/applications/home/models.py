# =====================================================================
# 📁 MODELOS · APP 'home'  (TPV DE TIENDA)
#   · Modulo              → on/off de módulos por URL (ModuloActivoMiddleware)
#   · MetodoPago          → catálogo usado por el TPV RESTAURANTE (tpv/)
#   · Venta               → venta del TPV → cliente (customer.Cliente),
#                           metodo_pago (payments.MetodoPago)
#   · DetalleVenta        → líneas: producto (product.Producto)
#   · Devolucion/Item     → NC interna de devolución (usa IVA de la venta)
#   · CajaArqueo          → arqueo del TPV
#   · ConfiguracionTPV    → datos de la tienda
#   · Comunicacion        → avisos
# Al completarse una venta se descuenta stock y se crean movimientos
# en cashflow (external_ref: tpv:venta:<id>[:efectivo|:tarjeta]).
# =====================================================================

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
    # Cliente de la venta (obligatorio si el pago es a FIADO)
    cliente = models.ForeignKey(
        'customer.Cliente', on_delete=models.PROTECT,
        null=True, blank=True, related_name='ventas',
        verbose_name="Cliente",
    )
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

    @property
    def base_imponible(self):
        return self.total - self.iva

    # --------------------------------------------------------
    # FIADO: lo que el cliente ya HA PAGADO de este ticket
    # --------------------------------------------------------
    @property
    def pagado_fiado(self):
        return sum(p.cantidad for p in self.pagos_fiado.all())

    # --------------------------------------------------------
    # FIADO: lo que queda por cobrar de ESTE ticket
    # (total menos los pagos a cuenta que ha hecho el cliente,
    #  menos lo ya devuelto por devoluciones/NC)
    # --------------------------------------------------------
    @property
    def pendiente_fiado(self):
        return max(0, (self.total or 0) - self.pagado_fiado - self.devuelto_total)

    # --------------------------------------------------------
    # DEVOLUCIONES (notas de crédito)
    # --------------------------------------------------------
    @property
    def devuelto_total(self):
        return sum(d.total for d in self.devoluciones.all())

    @property
    def estado_devolucion(self):
        if self.devuelto_total <= 0:
            return "ninguna"
        return "total" if self.devuelto_total >= (self.total or 0) else "parcial"

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
    moneda = models.CharField(max_length=10, default="C$")
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


class Devolucion(models.Model):
    """Nota de crédito (NC): devolución total o parcial de una venta."""
    venta = models.ForeignKey(Venta, on_delete=models.PROTECT, related_name="devoluciones", verbose_name="Venta")
    numero = models.CharField(max_length=12, unique=True, blank=True, verbose_name="Nº NC")
    motivo = models.CharField(max_length=200, verbose_name="Motivo")
    metodo_reembolso = models.CharField(
        max_length=20,
        choices=(("efectivo", "Efectivo"), ("tarjeta", "Tarjeta")),
        default="efectivo",
        verbose_name="Reembolso",
    )
    usuario = models.ForeignKey(User, on_delete=models.PROTECT, related_name="devoluciones", verbose_name="Usuario")
    total = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name="Total devuelto (IVA incl.)")
    iva = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name="IVA devuelto")
    creado_en = models.DateTimeField(auto_now_add=True, verbose_name="Fecha")

    class Meta:
        verbose_name = "Devolución"
        verbose_name_plural = "Devoluciones"
        ordering = ["-creado_en"]

    def __str__(self):
        return f"{self.numero} → {self.venta.codigo} ({self.total}€)"

    def save(self, *args, **kwargs):
        if not self.numero:
            n = Devolucion.objects.count() + 1
            self.numero = f"NC-{n:06d}"
        super().save(*args, **kwargs)

    @property
    def costo_devuelto(self):
        """Coste de compra de las unidades devueltan (vuelven a almacén)."""
        return sum(
            (i.cantidad * (i.detalle.producto.costo or 0)) for i in self.items.all()
        )


class DevolucionItem(models.Model):
    """Línea de una devolución: qué producto y cuántas unidades."""
    devolucion = models.ForeignKey(Devolucion, on_delete=models.CASCADE, related_name="items")
    detalle = models.ForeignKey(DetalleVenta, on_delete=models.PROTECT, related_name="devoluciones")
    cantidad = models.IntegerField(validators=[MinValueValidator(1)], verbose_name="Unidades")
    precio_unitario = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Precio ud. (IVA incl.)")
    subtotal = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Subtotal")

    class Meta:
        verbose_name = "Línea de devolución"
        verbose_name_plural = "Líneas de devolución"

    def __str__(self):
        return f"{self.cantidad}x {self.detalle.producto.nombre} ({self.devolucion.numero})"
