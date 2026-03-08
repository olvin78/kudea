from django.contrib import admin
from .models import MetodoPago

@admin.register(MetodoPago)
class MetodoPagoAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'activo', 'acepta_cambio']
    list_filter = ['activo', 'acepta_cambio']
    search_fields = ['nombre']
