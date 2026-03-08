from django.contrib import admin
from .models import Service, Ticket, TicketItem
from applications.product.models import Categoria, Producto
from django.contrib.admin.views.decorators import staff_member_required

# Registro de modelos básicos
admin.site.register(Service)

@staff_member_required
def solo_admin(request):
    ...

class TicketItemInline(admin.TabularInline):
    model = TicketItem
    extra = 0
    readonly_fields = ('product_name', 'quantity', 'price', 'total')
    can_delete = False

    def total(self, obj):
        if obj.quantity and obj.price:
            return obj.quantity * obj.price
        return "-"
    total.short_description = "Total (€)"


@admin.register(Ticket)
class TicketAdmin(admin.ModelAdmin):
    list_display = ('id', 'ticket_number', 'date', 'payment_method', 'total', 'closed')
    list_filter = ('payment_method', 'closed', 'date')
    search_fields = ('id', 'ticket_number')
    date_hierarchy = 'date'

    # Permitimos editar sólo el campo payment_method
    readonly_fields = ('date', 'total', 'closed')

    inlines = [TicketItemInline]

    def has_add_permission(self, request):
        return False  # No se permite crear tickets manualmente

    def has_change_permission(self, request, obj=None):
        return True  # Permitimos cambiar, pero los campos sensibles están protegidos por readonly_fields

    def has_delete_permission(self, request, obj=None):
        return False  # No se permite eliminar desde el admin
