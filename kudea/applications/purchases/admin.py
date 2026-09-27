# ============================================================
# REGISTROS EN EL DJANGO ADMIN (app: purchases)
#   - Proveedor: ficha de proveedores
#   - Compra: cabecera con las líneas embebidas (inline)
# ============================================================
from django.contrib import admin

from .models import Compra, CompraItem, Proveedor


# ---- PROVEEDORES ----
@admin.register(Proveedor)
class ProveedorAdmin(admin.ModelAdmin):
    list_display = ("nombre", "nit", "contacto", "telefono", "email", "activo")
    list_filter = ("activo",)
    search_fields = ("nombre", "nit", "contacto", "email")


# ---- LÍNEAS (dentro de la compra) ----
class CompraItemInline(admin.TabularInline):
    model = CompraItem
    extra = 1
    readonly_fields = ("subtotal", "iva_importe", "total")


# ---- COMPRAS ----
@admin.register(Compra)
class CompraAdmin(admin.ModelAdmin):
    list_display = ("numero", "proveedor", "fecha", "estado", "subtotal", "iva", "total")
    list_filter = ("estado", "fecha")
    search_fields = ("numero", "proveedor__nombre")
    readonly_fields = ("numero", "subtotal", "iva", "total", "creada_en")
    inlines = [CompraItemInline]
