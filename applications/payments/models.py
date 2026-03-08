from django.db import models

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
