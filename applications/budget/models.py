from django.db import models
from decimal import Decimal
from django.db.models import Sum  # ✅ IMPORTA SUM AQUÍ
from django.contrib.auth.models import User  # 👈 Importa el modelo de usuario
# Modelo para los clientes
from django.db import models



class Client(models.Model):
    nombre = models.CharField(max_length=255, blank=True, null=True)
    empresa = models.CharField(max_length=255, blank=True, null=True)  
    nif = models.CharField(max_length=20, unique=True, blank=True, null=True)
    email = models.EmailField(unique=True, blank=True, null=True)
    telefono = models.CharField(max_length=20, blank=True, null=True)
    direccion = models.TextField(blank=True, null=True)
    ciudad = models.CharField(max_length=100, blank=True, null=True)
    codigo_postal = models.CharField(max_length=10, blank=True, null=True)
    date_joined = models.DateField(auto_now_add=True, blank=True, null=True)  # 📌 Agrega esto si falta

    def __str__(self):
        return self.nombre if self.nombre else "Cliente sin nombre"


# Modelo para los presupuestos


class Budget(models.Model):
    cliente = models.ForeignKey('Client', on_delete=models.CASCADE, blank=True, null=True)
    agente = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)  # 👈 ESTE CAMPO DEBE ESTAR
    fecha_creacion = models.DateField(auto_now_add=True, blank=True, null=True)
    descripcion = models.TextField(blank=True, null=True)
    total = models.DecimalField(max_digits=10, decimal_places=2, default=0, blank=True, null=True)
    impuesto_porcentaje = models.DecimalField(max_digits=5, decimal_places=2, default=21.00, blank=True, null=True)


    @property
    def calcular_subtotal(self):
        """Calcula el subtotal sumando los valores de los ítems del presupuesto."""
        subtotal = self.items.aggregate(total=Sum('subtotal'))['total']
        return subtotal if subtotal is not None else Decimal(0)

    @property
    def calcular_impuestos(self):
        """Calcula los impuestos sobre el subtotal."""
        return (self.calcular_subtotal * self.impuesto_porcentaje) / Decimal(100)

    @property
    def calcular_total_con_impuestos(self):
        """Calcula el total final incluyendo impuestos."""
        return self.calcular_subtotal + self.calcular_impuestos

    def __str__(self):
        return f"Presupuesto #{self.id} - {self.cliente}"


class BudgetItem(models.Model):
    presupuesto = models.ForeignKey("Budget", on_delete=models.CASCADE, related_name="items")
    descripcion = models.CharField(max_length=255, blank=True, null=True)
    cantidad = models.PositiveIntegerField(default=1, blank=True, null=True)
    precio_unitario = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    descuento = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, blank=True, null=True)
    subtotal = models.DecimalField(max_digits=10, decimal_places=2, editable=True, blank=True, null=True)

    def save(self, *args, **kwargs):
        # ✅ Convertir valores a Decimal para evitar errores de tipo
        cantidad = Decimal(self.cantidad) if self.cantidad is not None else Decimal(1)
        precio_unitario = Decimal(self.precio_unitario) if self.precio_unitario is not None else Decimal(0.00)
        descuento = Decimal(self.descuento) if self.descuento is not None else Decimal(0.00)

        # ✅ Cálculo correcto del subtotal aplicando el descuento
        total_bruto = cantidad * precio_unitario
        descuento_aplicado = (descuento / Decimal(100)) * total_bruto  # Descuento en porcentaje
        self.subtotal = total_bruto - descuento_aplicado  # Resta el descuento

        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.descripcion} - {self.presupuesto.id}"
