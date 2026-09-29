# =====================================================================
# 📁 MODELOS · APP 'attendance'  (FICHAJES + NÓMINA)
#   · Punch      → fichajes (→ employee.Employee)
#   · ParteHoras → horas trabajadas × tarifa_hora congelada (nómina)
# =====================================================================

from django.db import models
from applications.employee.models import Employee  # <- reutilizas el modelo principal

class Punch(models.Model):
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE)
    clock_in = models.DateTimeField()
    clock_out = models.DateTimeField(null=True, blank=True)

    def duration(self):
        if self.clock_out:
            return self.clock_out - self.clock_in
        return None

    def __str__(self):
        return f"{self.employee} - {self.clock_in.strftime('%Y-%m-%d %H:%M')}"



class ParteHoras(models.Model):
    """Registro manual de horas trabajadas para el cierre de nómina.

    La tarifa se congela al crear el parte para que cambiar la tarifa
    del empleado no reescriba la historia de la nómina.
    """
    employee = models.ForeignKey(
        Employee, on_delete=models.CASCADE, related_name="partes_horas"
    )
    fecha = models.DateField()
    horas = models.DecimalField(
        max_digits=5, decimal_places=2,
        help_text="Horas trabajadas ese día (máx. 24)",
    )
    tarifa_hora = models.DecimalField(max_digits=6, decimal_places=2)
    notas = models.CharField(max_length=150, blank=True, default="")
    creado_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Parte de horas"
        verbose_name_plural = "Partes de horas"
        ordering = ["-fecha", "-id"]

    def __str__(self):
        return f"{self.employee} · {self.fecha} · {self.horas}h"

    @property
    def importe(self):
        return self.horas * self.tarifa_hora
