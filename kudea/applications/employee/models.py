from django.db import models
from django.contrib.auth.models import User
import random
import string

def generar_codigo_aleatorio(length=4):
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=length))

class Employee(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='employee')


    # Datos personales
    nombre = models.CharField(max_length=100)
    apellidos = models.CharField(max_length=100, blank=True, null=True)
    usuario = models.CharField(max_length=50, blank=True, null=True)
    codigo = models.CharField(max_length=50, unique=True, blank=True, editable=False)  # Código interno
    qr_token = models.CharField(max_length=64, unique=True, blank=True, null=True)

    # Identificadores para fichaje
    nfc_uid = models.CharField(max_length=32, unique=True, blank=True, null=True)

    # Contacto e identificación
    nif = models.CharField(max_length=15, blank=True, null=True)
    numero_seguridad_social = models.CharField(max_length=20, blank=True, null=True)
    telefono = models.CharField(max_length=15, blank=True, null=True)
    movil = models.CharField(max_length=15, blank=True, null=True)
    direccion = models.CharField(max_length=255, blank=True, null=True)
    cp = models.CharField(max_length=10, blank=True, null=True)
    poblacion = models.CharField(max_length=100, blank=True, null=True)
    provincia = models.CharField(max_length=100, blank=True, null=True)

    # Permisos TPV
    es_administrador = models.BooleanField(default=False)
    puede_realizar_salidas = models.BooleanField(default=False)
    puede_cambiar_fecha_hora = models.BooleanField(default=False)
    puede_modificar_ventas = models.BooleanField(default=False)
    puede_cambiar_subtotales = models.BooleanField(default=False)
    puede_cambiar_tarifa = models.BooleanField(default=False)

    # Estado
    esta_de_baja = models.BooleanField(default=False)
    fecha_baja = models.DateField(blank=True, null=True)
    observaciones = models.TextField(blank=True, null=True)

    # Auditoría
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    ultima_modificacion = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.nombre} {self.apellidos or ''}".strip()

    def save(self, *args, **kwargs):
        if not self.usuario:
            self.usuario = f"{self.nombre.lower().split()[0]}.{(self.apellidos or '').lower().split()[0]}"
        if not self.codigo:
            self.codigo = self.generate_codigo()
        if not self.qr_token:
            self.qr_token = self.generate_qr_token()
        super().save(*args, **kwargs)

    def generate_codigo(self):
        iniciales = ''.join([x[0] for x in self.nombre.strip().split()[:2] if x]).upper() or 'EMP'
        usuario_part = (self.usuario or self.user.username[:3]).strip().upper() or generar_codigo_aleatorio(2)
        aleatorio = generar_codigo_aleatorio(3)
        return f"{iniciales}-{usuario_part}{aleatorio}"

    def generate_qr_token(self):
        token = ''.join(random.choices(string.ascii_letters + string.digits, k=32))
        while Employee.objects.filter(qr_token=token).exists():
            token = ''.join(random.choices(string.ascii_letters + string.digits, k=32))
        return token

    @property
    def punch_code(self):
        """Alias para compatibilidad con otros módulos."""
        return self.codigo

