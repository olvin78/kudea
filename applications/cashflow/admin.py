from django.contrib import admin
from .models import Cuenta, Movimiento


@admin.register(Cuenta)
class CuentaAdmin(admin.ModelAdmin):
    list_display = ("nombre", "activa", "saldo")
    list_filter = ("activa",)
    search_fields = ("nombre",)


@admin.register(Movimiento)
class MovimientoAdmin(admin.ModelAdmin):
    list_display = (
        "fecha",
        "concepto",
        "cuenta",
        "tipo",
        "metodo_pago",
        "cantidad",
        "created_by",
        "origen",
    )

    list_filter = (
        "tipo",
        "metodo_pago",
        "cuenta",
        "origen",
        "fecha",
    )

    search_fields = ("concepto", "external_ref")

    readonly_fields = ("fecha",)

    ordering = ("-fecha",)