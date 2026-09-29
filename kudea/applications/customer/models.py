# applications/customer/models.py
# ============================================================
#  CLIENTES y FIADO (cuenta corriente de cliente)
#   - Cliente: alta rápida desde el TPV (sólo hace falta nombre)
#   - PagoFiado: abonos a cuenta de un ticket de fiado
# ============================================================

from django.conf import settings
from django.db import models


class Cliente(models.Model):
    """Cliente de la tienda.

    El DNI/correo/teléfono son OPCIONALES para poder dar de alta desde el
    TPV en 2 segundos (sólo el nombre es obligatorio).
    """
    nombre = models.CharField(max_length=255)
    dni = models.CharField(max_length=20, unique=True, blank=True, null=True)
    codigo_postal = models.CharField(max_length=5, blank=True, default="")
    correo = models.EmailField(blank=True, default="")
    telefono = models.CharField(max_length=30, blank=True, default="")
    creado_en = models.DateTimeField(auto_now_add=True, null=True, blank=True)

    class Meta:
        verbose_name = "Cliente"
        verbose_name_plural = "Clientes"
        ordering = ["nombre"]

    def __str__(self):
        return self.nombre

    # --------------------------------------------------------
    # Saldo del fiado: lo que DEBE menos lo que ya HA PAGADO
    # --------------------------------------------------------
    @property
    def saldo_fiado(self):
        from applications.home.models import Venta

        debe = (
            Venta.objects.filter(
                cliente=self, metodo_pago__nombre__iexact="Fiado"
            )
            .exclude(estado="cancelada")
            .aggregate(t=models.Sum("total"))["t"]
            or 0
        )
        pagado = (
            PagoFiado.objects.filter(venta__cliente=self)
            .aggregate(t=models.Sum("cantidad"))["t"]
            or 0
        )
        return debe - pagado


class PagoFiado(models.Model):
    """Pago (total o parcial) de un ticket de fiado.

    Cuando el cliente paga se crea UN ESTE REGISTRO y se registra el
    dinero en caja (ingreso). Así el saldo baja y el arqueo cuadra.
    """
    venta = models.ForeignKey(
        "home.Venta", related_name="pagos_fiado", on_delete=models.CASCADE
    )
    cantidad = models.DecimalField(max_digits=10, decimal_places=2)
    metodo_pago = models.ForeignKey(
        "payments.MetodoPago", on_delete=models.PROTECT, null=True, blank=True
    )
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, null=True, blank=True
    )
    creado_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Pago de fiado"
        verbose_name_plural = "Pagos de fiado"
        ordering = ["-creado_en"]

    def __str__(self):
        return f"Pago {self.cantidad}€ → {self.venta.codigo}"
