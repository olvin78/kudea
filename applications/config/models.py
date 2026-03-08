from django.db import models


# Create your models here.

class ConfiguracionFiscal(models.Model):
    nombre = models.CharField(max_length=100, default="Configuración General")
    iva_general = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=21.00
    )
    fondo_caja_defecto = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=200.00,
        verbose_name="Fondo de Caja (Defecto)"
    )

    class Meta:
        verbose_name = "Configuración"
        verbose_name_plural = "Configuraciones"

    def __str__(self):
        return f"{self.nombre} - IVA {self.iva_general}%"