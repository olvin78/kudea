# ============================================================
# COMPRAS Y PROVEEDORES  (app: purchases)
# ------------------------------------------------------------
# Módulo de adquisiciones: quién te vende, qué le compras y
# a qué precio. Alimenta el stock y el "libro de compras".
#
# SECCIONES DE ESTE FICHERO:
#   1) PROVEEDORES -> ficha del proveedor (nombre, NIT, contacto)
#   2) COMPRAS     -> cabecera del pedido (nº, estado, totales)
#   3) LÍNEAS      -> producto + cantidad + precio de compra + IVA
#
# NOTA DE IVA: los precios de compra se guardan SIN IVA (base),
# igual que en una factura de proveedor. La IVA soportado se
# calcula por línea y el total de la compra = base + IVA.
# (En las VENTAS el precio va con IVA incluido: es el PVP.)
# ============================================================

from decimal import Decimal, ROUND_HALF_UP

from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models
from django.utils import timezone


def _centimos(valor):
    """Redondea un importe monetario a 2 decimales (banco/taquilla)."""
    return valor.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


# ============================================================
# 1) PROVEEDORES — quién te vende la mercancía
# ============================================================
class Proveedor(models.Model):
    nombre = models.CharField(max_length=150, unique=True)
    nit = models.CharField("NIT / NIF / CIF", max_length=30, blank=True, null=True)
    contacto = models.CharField(max_length=150, blank=True, null=True)
    telefono = models.CharField(max_length=30, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    direccion = models.CharField(max_length=255, blank=True, null=True)
    dias_entrega = models.CharField(
        max_length=100, blank=True, null=True,
        help_text="Ej: lunes y jueves"
    )
    activo = models.BooleanField(default=True)
    notas = models.TextField(blank=True, null=True)
    creado_en = models.DateTimeField(auto_now_add=True)
    actualizado_en = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Proveedor"
        verbose_name_plural = "Proveedores"
        ordering = ["nombre"]

    def __str__(self):
        return self.nombre

    @property
    def compras_count(self):
        """Nº de compras registradas a este proveedor (para la ficha)."""
        return self.compras.count()


# ============================================================
# 2) COMPRAS — cabecera del pedido / factura de proveedor
#     estados: borrador -> recibida (subió stock)
#              borrador -> cancelada (no se recibe)
# ============================================================
class Compra(models.Model):
    ESTADOS = (
        ("borrador", "Borrador"),
        ("recibida", "Recibida"),
        ("cancelada", "Cancelada"),
    )

    numero = models.CharField(max_length=20, unique=True, blank=True, editable=False)
    proveedor = models.ForeignKey(
        Proveedor, related_name="compras", on_delete=models.PROTECT
    )
    fecha = models.DateField(default=timezone.localdate, help_text="Fecha del pedido / factura")
    estado = models.CharField(max_length=20, choices=ESTADOS, default="borrador")

    # Totales: subtotal = BASE sin IVA · iva = cuota · total = base + cuota
    subtotal = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    iva = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    notas = models.TextField(blank=True, null=True)
    creada_por = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True,
        on_delete=models.SET_NULL, related_name="compras_creadas"
    )
    creada_en = models.DateTimeField(auto_now_add=True)
    recibida_en = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = "Compra"
        verbose_name_plural = "Compras"
        ordering = ["-creada_en"]

    def __str__(self):
        return f"{self.numero} · {self.proveedor.nombre}"

    def save(self, *args, **kwargs):
        # Nº automático al estilo de las ventas: COM-000001, COM-000002...
        if not self.numero:
            ultima = Compra.objects.order_by("-id").first()
            ultimo_id = ultima.id if ultima else 0
            self.numero = f"COM-{ultimo_id + 1:06d}"
        super().save(*args, **kwargs)

    def recalcular(self):
        """Vuelve a sumar las líneas y guarda los totales de la cabecera.

        Usa queryset.update() para no volver a llamar a save()
        y crear un bucle con el save() de las líneas.
        """
        subtotal = Decimal("0")
        iva = Decimal("0")
        for item in self.items.all():
            subtotal += item.subtotal
            iva += item.iva_importe

        Compra.objects.filter(pk=self.pk).update(
            subtotal=_centimos(subtotal),
            iva=_centimos(iva),
            total=_centimos(subtotal + iva),
        )
        self.subtotal = _centimos(subtotal)
        self.iva = _centimos(iva)
        self.total = _centimos(subtotal + iva)

    @property
    def recibida(self):
        return self.estado == "recibida"


# ============================================================
# 3) LÍNEAS DE COMPRA — qué producto, cuántas unidades y a qué precio
# ============================================================
class CompraItem(models.Model):
    compra = models.ForeignKey(Compra, related_name="items", on_delete=models.CASCADE)
    producto = models.ForeignKey(
        "product.Producto", on_delete=models.PROTECT, related_name="compras_items"
    )
    cantidad = models.PositiveIntegerField(validators=[MinValueValidator(1)])
    # Precio de compra POR UNIDAD sin IVA (como aparece en la factura)
    precio_unitario = models.DecimalField(
        max_digits=10, decimal_places=2, validators=[MinValueValidator(0)]
    )
    # % que cobra el proveedor: NULL = no indicado (se hereda del producto en save()).
    # Un 0 explícito significa producto EXENTO de IVA.
    porcentaje_iva = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True, default=None)

    # Totales de la línea (se recalculan solos en save())
    subtotal = models.DecimalField(max_digits=12, decimal_places=2, default=0)      # base
    iva_importe = models.DecimalField(max_digits=12, decimal_places=2, default=0)   # cuota
    total = models.DecimalField(max_digits=12, decimal_places=2, default=0)         # base + cuota

    class Meta:
        verbose_name = "Línea de compra"
        verbose_name_plural = "Líneas de compra"
        ordering = ["id"]

    def __str__(self):
        return f"{self.cantidad} x {self.producto.nombre} @ {self.precio_unitario}"

    def save(self, *args, **kwargs):
        # Si no se indicó IVA (NULL), se toma el del producto
        if self.porcentaje_iva is None:
            self.porcentaje_iva = self.producto.porcentaje_iva or Decimal("0")

        base = Decimal(self.cantidad) * self.precio_unitario
        self.subtotal = _centimos(base)
        self.iva_importe = _centimos(base * self.porcentaje_iva / Decimal("100"))
        self.total = _centimos(self.subtotal + self.iva_importe)

        super().save(*args, **kwargs)

        # Mantiene los totales de la cabecera al día
        if self.compra_id:
            self.compra.recalcular()
