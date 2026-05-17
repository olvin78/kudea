# applications/attendance/models.py
import random
import string
from django.db import models
from django.contrib.auth.models import User


class Employee(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)  # Relacionado con el modelo User de Django
    punch_code = models.CharField(max_length=10, unique=True, blank=True)  # Código para fichaje
    nfc_uid = models.CharField(max_length=32, unique=True, blank=True, null=True)  # NFC UID
    qr_token = models.CharField(max_length=64, unique=True, blank=True, null=True)  # QR Token para fichaje

    def __str__(self):
        return self.user.get_full_name()

    def save(self, *args, **kwargs):
        if not self.punch_code:
            self.punch_code = self.generate_code()  # Generación automática del código de fichaje
        if not self.qr_token:
            self.qr_token = self.generate_qr_token()  # Generación automática del token QR
        super().save(*args, **kwargs)

    def generate_code(self):
        base = self.user.username[:3].upper()  # Primeros tres caracteres del nombre de usuario
        suffix = ''.join(random.choices(string.ascii_uppercase + string.digits, k=4))  # Sufijo aleatorio
        code = f"{base}{suffix}"  # Código final
        while Employee.objects.filter(punch_code=code).exists():  # Asegura que el código sea único
            suffix = ''.join(random.choices(string.ascii_uppercase + string.digits, k=4))
            code = f"{base}{suffix}"
        return code

    def generate_qr_token(self):
        token = ''.join(random.choices(string.ascii_letters + string.digits, k=32))  # Generación del token QR
        while Employee.objects.filter(qr_token=token).exists():  # Asegura que el token sea único
            token = ''.join(random.choices(string.ascii_letters + string.digits, k=32))
        return token


class Punch(models.Model):
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE)  # Relación con Employee
    clock_in = models.DateTimeField()  # Hora de entrada
    clock_out = models.DateTimeField(null=True, blank=True)  # Hora de salida

    def duration(self):
        if self.clock_out:
            return self.clock_out - self.clock_in  # Calcula la duración del fichaje
        return None
