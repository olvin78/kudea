
from django.contrib import admin
from .models import ConfiguracionFiscal

@admin.register(ConfiguracionFiscal)
class ConfiguracionFiscalAdmin(admin.ModelAdmin):
    list_display = ("nombre", "iva_general")