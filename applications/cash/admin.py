from django.contrib import admin
from .models import AperturaCaja, CierreCaja

@admin.register(AperturaCaja)
class AperturaCajaAdmin(admin.ModelAdmin):
    list_display = ('fecha', 'hora_apertura', 'usuario', 'fondo_inicial')
    list_filter = ('fecha', 'usuario')
    search_fields = ('usuario__username', 'usuario__first_name', 'usuario__last_name')
    date_hierarchy = 'fecha'

@admin.register(CierreCaja)
class CierreCajaAdmin(admin.ModelAdmin):
    list_display = ('fecha', 'tipo', 'hora_cierre', 'usuario', 'total_ventas', 'efectivo_esperado', 'efectivo_retirado')
    list_filter = ('tipo', 'fecha', 'usuario')
    search_fields = ('usuario__username', 'usuario__first_name')
    date_hierarchy = 'fecha'
    readonly_fields = ('fecha', 'tipo', 'fecha_inicio', 'fecha_fin', 'hora_cierre', 'usuario', 'fondo_inicial', 'efectivo_esperado', 'efectivo_retirado', 'total_ventas')

