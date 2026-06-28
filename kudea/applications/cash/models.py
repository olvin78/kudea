from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


class Caja(models.Model):
    nombre = models.CharField(max_length=100, unique=True, verbose_name="Nombre de la caja")
    pin = models.CharField(max_length=4, default="1234", verbose_name="PIN de apertura")
    activa = models.BooleanField(default=True, verbose_name="Activa")
    predeterminada = models.BooleanField(default=False, verbose_name="Caja por defecto")
    creado_en = models.DateTimeField(auto_now_add=True, verbose_name="Creado")

    class Meta:
        verbose_name = "Caja"
        verbose_name_plural = "Cajas"
        ordering = ['nombre']

    def __str__(self):
        return self.nombre


class AperturaCaja(models.Model):
    """
    Registra la apertura de caja al inicio del turno/día.
    El cajero introduce el fondo inicial (dinero con el que arranca la caja).
    """
    ESTADOS = (
        ('abierta', 'Abierta'),
        ('pausada', 'Pausada'),
        ('cerrada', 'Cerrada'),
    )

    usuario     = models.ForeignKey(User, on_delete=models.PROTECT,
                                    related_name='aperturas', verbose_name='Cajero')
    fondo_inicial = models.DecimalField(
        max_digits=10, decimal_places=2,
        verbose_name='Fondo inicial (€)',
        help_text='Importe en efectivo con el que se abre la caja.'
    )
    fecha       = models.DateField(default=timezone.localdate, verbose_name='Fecha')
    caja = models.ForeignKey(Caja, on_delete=models.PROTECT, null=True, blank=True, related_name='aperturas', verbose_name='Caja')
    hora_apertura = models.DateTimeField(auto_now_add=True, verbose_name='Hora apertura')
    hora_cierre   = models.DateTimeField(null=True, blank=True, verbose_name='Hora cierre')
    estado      = models.CharField(max_length=10, choices=ESTADOS, default='abierta')
    notas       = models.TextField(blank=True, null=True, verbose_name='Notas')

    class Meta:
        verbose_name = 'Apertura de Caja'
        verbose_name_plural = 'Aperturas de Caja'
        ordering = ['-fecha', '-hora_apertura']

    def __str__(self):
        return f"Apertura {self.fecha} — {self.usuario.username} — Fondo: {self.fondo_inicial}€"

    @property
    def esta_abierta(self):
        return self.estado == 'abierta'


class CierreCaja(models.Model):
    """
    Guarda el informe final del cuadre de caja del día o periodo para mantener un registro histórico.
    """
    TIPOS = (
        ('diario', 'Diario'),
        ('semanal', 'Semanal'),
        ('mensual', 'Mensual'),
        ('anual', 'Anual'),
        ('personalizado', 'Personalizado'),
    )
    
    tipo = models.CharField(max_length=20, choices=TIPOS, default='diario', verbose_name="Tipo de Cierre")
    fecha_inicio = models.DateField(default=timezone.localdate, verbose_name="Fecha Desde")
    fecha_fin = models.DateField(default=timezone.localdate, verbose_name="Fecha Hasta")
    
    fecha = models.DateField(default=timezone.localdate, verbose_name="Fecha de Registro")
    hora_cierre = models.DateTimeField(auto_now_add=True, verbose_name="Hora del Registro")
    usuario = models.ForeignKey(User, on_delete=models.PROTECT, verbose_name="Usuario / Cajero")
    caja = models.ForeignKey(Caja, on_delete=models.PROTECT, null=True, blank=True, related_name='cierres', verbose_name="Caja")
    
    fondo_inicial = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Fondo Inicial")
    efectivo_esperado = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Efectivo Esperado (Cajón)")
    efectivo_retirado = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Efectivo Retirado (Neto)")
    total_ventas = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Total Ventas del Periodo")
    
    notas = models.TextField(blank=True, null=True, verbose_name="Incidencias / Notas")

    class Meta:
        verbose_name = "Cierre de Caja"
        verbose_name_plural = "Cierres de Caja"
        ordering = ['-fecha_fin', '-hora_cierre']

    def __str__(self):
        return f"Cierre {self.fecha} - {self.total_ventas}€ ventas - {self.usuario.username}"
