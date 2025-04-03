from django.db import models




class Ticket(models.Model):
    campo1 = models.CharField(max_length=100)
    campo2 = models.CharField(max_length=100)
    campo3 = models.TextField()

    def __str__(self):
        return self.campo1  # Esto es solo un ejemplo
