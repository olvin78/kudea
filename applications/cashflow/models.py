from decimal import Decimal
from django.db import models
from django.utils import timezone
from django.conf import settings


class Cuenta(models.Model):
    nombre = models.CharField(max_length=100, unique=True)
    iban = models.CharField(max_length=34, blank=True, null=True)
    numero_cuenta = models.CharField(max_length=34, blank=True, null=True)
    entidad = models.CharField(max_length=100, blank=True, null=True)
    activa = models.BooleanField(default=True)

    class Meta:
        ordering = ["nombre"]

    def __str__(self):
        return self.nombre

    @property
    def saldo(self):
        total = Decimal("0.00")
        for m in self.movimientos.all():
            total += m.signed_amount()
        return total


class Movimiento(models.Model):

    class Tipo(models.TextChoices):
        INGRESO = "ingreso", "Ingreso"
        GASTO = "gasto", "Gasto"
        AJUSTE = "ajuste", "Ajuste"
        TRANSFERENCIA = "transferencia", "Transferencia"

    class Origen(models.TextChoices):
        TPV = "tpv", "TPV"
        FACTURA = "factura", "Factura"
        ARQUEO = "arqueo", "Arqueo"
        MANUAL = "manual", "Manual"
        SISTEMA = "sistema", "Sistema"

    class MetodoPago(models.TextChoices):
        EFECTIVO = "efectivo", "Efectivo"
        TRANSFERENCIA = "transferencia", "Transferencia"
        TARJETA = "tarjeta", "Tarjeta"
        BIZUM = "bizum", "Bizum"

    class CanalOperacion(models.TextChoices):
        DIRECTA = "directa", "Venta Directa"
        SUSCRIPCION = "suscripcion", "Suscripción"
        REEMBOLSO = "reembolso", "Reembolso"
        OTROS = "otros", "Otros"

    fecha = models.DateTimeField(default=timezone.now)
    concepto = models.CharField(max_length=255)
    tipo = models.CharField(max_length=20, choices=Tipo.choices)
    origen = models.CharField(max_length=20, choices=Origen.choices, default=Origen.MANUAL)
    cuenta = models.ForeignKey(Cuenta, on_delete=models.PROTECT, related_name="movimientos")
    cantidad = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))
    metodo_pago = models.CharField(max_length=20, choices=MetodoPago.choices, default=MetodoPago.EFECTIVO)
    canal_operacion = models.CharField(max_length=20, choices=CanalOperacion.choices, default=CanalOperacion.DIRECTA)
    external_ref = models.CharField(max_length=120, blank=True, null=True, db_index=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)

    class Meta:
        indexes = [
            models.Index(fields=["origen", "external_ref"]),
            models.Index(fields=["fecha"]),
        ]
        ordering = ["-fecha", "-id"]

    def __str__(self):
        return f"{self.get_tipo_display()} - {self.concepto} - {self.cantidad} - {self.get_metodo_pago_display()}"

    def signed_amount(self) -> Decimal:
        """
        Devuelve la cantidad con signo real según tipo.
        """
        if self.tipo == self.Tipo.INGRESO:
            return self.cantidad
        if self.tipo in (self.Tipo.GASTO, self.Tipo.AJUSTE):
            return -self.cantidad
        if self.tipo == self.Tipo.TRANSFERENCIA:
            return Decimal("0.00")
        return Decimal("0.00")