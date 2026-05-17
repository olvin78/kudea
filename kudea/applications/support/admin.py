from django.contrib import admin
from .models import Ticket, TipoTicket

@admin.register(TipoTicket)
class TipoTicketAdmin(admin.ModelAdmin):
    list_display = ('nombre',)
    search_fields = ('nombre',)

@admin.register(Ticket)
class TicketAdmin(admin.ModelAdmin):
    list_display = (
        'identificador', 'cliente', 'tipo', 'asunto',
        'estado', 'prioridad', 'ultima_respuesta',
        'actualizado', 'creado'
    )
    list_filter = ('estado', 'prioridad', 'tipo', 'creado')
    search_fields = ('identificador', 'asunto', 'cliente__username', 'tipo__nombre')
    ordering = ('-actualizado',)
    readonly_fields = ('identificador', 'actualizado', 'creado')

    fieldsets = (
        (None, {
            'fields': (
                'identificador',
                'cliente',
                'tipo',
                'asunto',
                'descripcion',
                'archivo',  # 👈 lo agregamos aquí
                'estado',
                'prioridad',
            )
        }),
        ('Fechas', {
            'fields': ('ultima_respuesta', 'actualizado', 'creado'),
        }),
    )
