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
