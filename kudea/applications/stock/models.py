from django.db import models
from django.utils import timezone
from django.db import transaction
from applications.product.models import Producto


class Movement(models.Model):
    producto = models.ForeignKey(
        Producto,
        on_delete=models.PROTECT,
        related_name='movimientos_stock'
    )
    cantidad = models.IntegerField()
    tipo = models.CharField(
        max_length=10,
        choices=[('entrada', 'Entrada'), ('salida', 'Salida')]
    )
    fecha = models.DateTimeField(default=timezone.now)
    observaciones = models.TextField(blank=True, null=True)

    class Meta:
        ordering = ['-fecha', '-id']

    def __str__(self):
        return f"{self.get_tipo_display()} - {self.producto.nombre} ({self.cantidad})"

    @transaction.atomic
    def save(self, *args, **kwargs):
        is_new = self.pk is None

        if is_new:
            if self.tipo == 'entrada':
                self.producto.stock += self.cantidad
            elif self.tipo == 'salida':
                if self.producto.stock < self.cantidad:
                    raise ValueError("Stock insuficiente")
                self.producto.stock -= self.cantidad

            self.producto.save(update_fields=['stock'])

        super().save(*args, **kwargs)