from django.contrib import admin
from django.utils.html import format_html
from .models import Producto, Categoria

class StockFilter(admin.SimpleListFilter):
    title = 'Stock'
    parameter_name = 'stock'

    def lookups(self, request, model_admin):
        return (
            ('bajo', 'Stock bajo'),
            ('optimo', 'Stock óptimo'),
            ('agotado', 'Agotado'),
        )

    def queryset(self, request, queryset):
        from django.db.models import F
        if self.value() == 'bajo':
            return queryset.filter(stock__lt=F('stock_minimo'))
        if self.value() == 'optimo':
            return queryset.filter(stock__gte=F('stock_minimo'))
        if self.value() == 'agotado':
            return queryset.filter(stock=0)


@admin.register(Categoria)
class CategoriaAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'productos_count', 'creado_en']
    search_fields = ['nombre']

    def productos_count(self, obj):
        return obj.products.count()
    productos_count.short_description = 'Productos'


@admin.register(Producto)
class ProductoAdmin(admin.ModelAdmin):
    list_display = ['codigo_barras', 'nombre', 'categoria', 'precio', 'porcentaje_iva', 'descuento', 'stock', 'stock_status', 'activo', 'creado_en']
    list_filter = [StockFilter, 'categoria', 'activo', 'creado_en', 'actualizado_en']
    search_fields = ['nombre', 'codigo_barras']
    list_editable = ['precio', 'porcentaje_iva', 'descuento', 'stock', 'activo']
    actions = ['activar_productos', 'desactivar_productos']
    readonly_fields = ['imagen_preview', 'creado_en', 'actualizado_en']
    fieldsets = (
        (None, {
            'fields': ('codigo_barras', 'nombre', 'categoria', 'activo')
        }),
        ('Precios y Stock', {
            'fields': ('precio', 'porcentaje_iva', 'descuento', 'costo', 'stock', 'stock_minimo')
        }),
        ('Imagen', {
            'fields': ('imagen', 'imagen_preview')
        }),
        ('Fechas', {
            'fields': ('creado_en', 'actualizado_en')
        }),
    )

    def imagen_preview(self, obj):
        return format_html('<img src="{}" style="max-height: 200px;"/>', obj.imagen.url) if obj.imagen else "-"
    imagen_preview.short_description = 'Vista previa'

    def stock_status(self, obj):
        if obj.stock == 0:
            color = 'red'
            text = 'Agotado'
        elif obj.stock < obj.stock_minimo:
            color = 'orange'
            text = 'Bajo'
        else:
            color = 'green'
            text = 'Óptimo'
        return format_html('<span style="color: {};">{}</span>', color, text)
    stock_status.short_description = 'Estado stock'

    def activar_productos(self, request, queryset):
        updated = queryset.update(activo=True)
        self.message_user(request, f'{updated} productos activados')
    activar_productos.short_description = 'Activar productos seleccionados'

    def desactivar_productos(self, request, queryset):
        updated = queryset.update(activo=False)
        self.message_user(request, f'{updated} productos desactivados')
    desactivar_productos.short_description = 'Desactivar productos seleccionados'