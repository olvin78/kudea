from django.contrib import admin
from .models import Category, Product, Service, Ticket, TicketItem

# Registro de los modelos en el admin
admin.site.register(Category)
admin.site.register(Product)
admin.site.register(Service)




class TicketItemInline(admin.TabularInline):
    model = TicketItem
    extra = 0
    readonly_fields = ('product_name', 'quantity', 'price', 'total')
    can_delete = False

    def total(self, obj):
        return obj.quantity * obj.price
    total.short_description = "Total (€)"


@admin.register(Ticket)
class TicketAdmin(admin.ModelAdmin):
    list_display = ('id', 'date', 'payment_method', 'total', 'closed')
    list_filter = ('payment_method', 'closed', 'date')
    search_fields = ('id',)
    date_hierarchy = 'date'
    readonly_fields = ('date', 'total', 'payment_method', 'closed')
    inlines = [TicketItemInline]

    def has_add_permission(self, request):
        return False  # No se permite crear tickets manualmente desde el admin

    def has_change_permission(self, request, obj=None):
        return False  # Solo lectura

    def has_delete_permission(self, request, obj=None):
        return False  # Solo lectura
