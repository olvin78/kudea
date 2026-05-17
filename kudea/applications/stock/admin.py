from django.contrib import admin
from .models import Movement


# Register your models here.



@admin.register(Movement)
class MovementAdmin(admin.ModelAdmin):
    list_display = ('fecha', 'producto', 'tipo', 'cantidad')
    list_filter = ('tipo', 'fecha')
    search_fields = ('producto', 'observaciones')
    date_hierarchy = 'fecha'
