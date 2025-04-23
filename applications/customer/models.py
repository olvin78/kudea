# applications/customer/models.py

from django.db import models

class Cliente(models.Model):
    nombre = models.CharField(max_length=255)
    dni = models.CharField(max_length=9, unique=True)  # Asegúrate de que el DNI sea único
    codigo_postal = models.CharField(max_length=5)
    correo = models.EmailField()
    telefono = models.CharField(max_length=15)

    def __str__(self):
        return self.nombre
