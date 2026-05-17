from django.contrib import admin

# Importamos todos los modelos que vamos a gestionar desde el panel admin
from .models import MetodoPago, Venta, DetalleVenta, Comunicacion, ConfiguracionTPV, Modulo


# ============================================================
# 🔹 INLINE: Detalles dentro de una Venta
# ============================================================
# Esto permite que cuando entres a una venta,
# puedas ver los productos vendidos dentro de esa venta.
# Se muestran en formato tabla dentro del formulario.

class DetalleVentaInline(admin.TabularInline):
    model = DetalleVenta  # Modelo relacionado
    extra = 0  # No mostrar líneas vacías extra
    readonly_fields = (
        'producto',
        'cantidad',
        'precio_unitario',
        'total'
    )  # No se pueden modificar desde aquí


# ============================================================
# 🔹 ADMIN DE VENTAS
# ============================================================
# Configura cómo se ve el modelo Venta en el admin

@admin.register(Venta)
class VentaAdmin(admin.ModelAdmin):

    # Columnas visibles en la lista de ventas
    list_display = (
        'codigo',
        'usuario',
        'metodo_pago',
        'total',
        'estado',
        'creado_en'
    )

    # Filtros laterales
    list_filter = (
        'estado',
        'metodo_pago',
        'creado_en'
    )

    # Buscador superior
    search_fields = (
        'codigo',
        'usuario__username'
    )

    # Permite navegar por fecha (año / mes / día)
    date_hierarchy = 'creado_en'

    # Campos que no se pueden modificar manualmente
    readonly_fields = (
        'codigo',
        'subtotal',
        'iva',
        'total',
        'recibido',
        'cambio'
    )

    # Mostrar los productos vendidos dentro de cada venta
    inlines = [DetalleVentaInline]


# ============================================================
# 🔹 CONFIGURACIÓN GENERAL DEL TPV
# ============================================================
# Solo debería existir una configuración
# (Tu modelo ya lo controla con validación en save())

@admin.register(ConfiguracionTPV)
class ConfiguracionTPVAdmin(admin.ModelAdmin):

    # Qué columnas se muestran en la lista
    list_display = (
        'nombre_tienda',
        'iva_por_defecto',
        'moneda',
        'actualizado_en'
    )

    # Campo solo lectura
    readonly_fields = ('actualizado_en',)


# ============================================================
# 🔹 MÓDULOS ACTIVABLES / DESACTIVABLES
# ============================================================
# Este modelo controla qué partes del sistema están activas.
# Sirve para:
# - Desactivar módulos visualmente
# - Bloquear acceso real a vistas
# - Crear planes tipo "Básico / Pro"

@admin.register(Modulo)
class ModuloAdmin(admin.ModelAdmin):

    # Columnas visibles
    list_display = (
        'nombre',   # Nombre visible (ej: Facturas)
        'clave',    # Identificador interno (ej: facturas)
        'activo'    # Estado ON/OFF
    )

    # Permite activar/desactivar directamente desde la lista
    list_editable = ('activo',)

    # Buscador
    search_fields = ('nombre', 'clave')


@admin.register(Comunicacion)
class ComunicacionAdmin(admin.ModelAdmin):
    list_display = ('titulo', 'emisor', 'creado_en')
    list_filter = ('creado_en', 'emisor')
    search_fields = ('titulo', 'contenido')
    filter_horizontal = ('visto_por',)
    
    def save_model(self, request, obj, form, change):
        if not obj.pk:
            obj.emisor = request.user
        super().save_model(request, obj, form, change)