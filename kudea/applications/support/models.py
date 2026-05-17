from django.db import models
from django.contrib.auth.models import User


class TipoTicket(models.Model):
    nombre = models.CharField(max_length=100, unique=True,null=True, blank=True)

    def __str__(self):
        return self.nombre


class Ticket(models.Model):
    class Estado(models.TextChoices):
        ABIERTO = 'abierto', 'Abierto'
        EN_PROGRESO = 'en_progreso', 'En progreso'
        CERRADO = 'cerrado', 'Cerrado'

    class Prioridad(models.TextChoices):
        BAJA = 'baja', 'Baja'
        MEDIA = 'media', 'Media'
        ALTA = 'alta', 'Alta'
        URGENTE = 'urgente', 'Urgente'

    identificador = models.CharField(max_length=10, unique=True, editable=False,null=True, blank=True)
    cliente = models.ForeignKey(User, on_delete=models.CASCADE, related_name='tickets',null=True, blank=True)
    tipo = models.ForeignKey(TipoTicket, on_delete=models.SET_NULL, null=True, blank=True, related_name='tickets')
    asunto = models.CharField(max_length=255,null=True, blank=True)
    estado = models.CharField(max_length=20, choices=Estado.choices, default=Estado.ABIERTO)
    prioridad = models.CharField(max_length=10, choices=Prioridad.choices, default=Prioridad.MEDIA,null=True, blank=True)
    ultima_respuesta = models.DateTimeField(null=True, blank=True)
    actualizado = models.DateTimeField(auto_now=True,null=True, blank=True)
    creado = models.DateTimeField(auto_now_add=True,null=True, blank=True)
    descripcion = models.TextField(null=True, blank=True)
    archivo = models.FileField(upload_to='support/archivos/', null=True, blank=True)


    def __str__(self):
        return f"{self.identificador} - {self.asunto}"

    def save(self, *args, **kwargs):
        if not self.identificador:
            from secrets import token_hex
            while True:
                code = f"TCK-{token_hex(3).upper()}"
                if not Ticket.objects.filter(identificador=code).exists():
                    self.identificador = code
                    break
        super().save(*args, **kwargs)


