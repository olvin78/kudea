from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


class AperturaCaja(models.Model):
    """
    Registra la apertura de caja al inicio del turno/día.
    El cajero introduce el fondo inicial (dinero con el que arranca la caja).
    """
    ESTADOS = (
        ('abierta', 'Abierta'),
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
