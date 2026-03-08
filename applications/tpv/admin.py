from django.contrib import admin
from .models import Mesa, Comanda, ComandaItem, Empleado
#from applications.product.models import Product, Category
# Register your models here.



"""class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'price', 'category', 'image')
    list_filter = ('category',)
    search_fields = ('name',)

# Registra el modelo Product
admin.site.register(Product, ProductAdmin)
admin.site.register(Mesa)
admin.site.register(Comanda)
admin.site.register(ComandaItem)
admin.site.register(Category)"""





@admin.register(Empleado)
class EmpleadoAdmin(admin.ModelAdmin):
    list_display = ('codigo', 'nombre', 'usuario', 'email', 'es_administrador', 'esta_de_baja', 'ultima_modificacion')
    readonly_fields = ('codigo', 'fecha_creacion', 'ultima_modificacion')  # 👈 agregamos 'codigo' como readonly

    fieldsets = (
        ('Datos personales', {
            'fields': ('nombre', 'apellidos', 'nif', 'usuario', 'email', 'telefono', 'movil', 'direccion', 'cp', 'poblacion', 'provincia')
        }),
        ('Código de empleado', {  # 👈 nueva sección o si prefieres lo puedes meter arriba
            'fields': ('codigo',),
        }),
        ('Permisos', {
            'fields': (
                'es_administrador',
                'puede_realizar_salidas',
                'puede_cambiar_fecha_hora',
                'puede_modificar_ventas',
                'puede_cambiar_subtotales',
                'puede_cambiar_tarifa',
            )
        }),
        ('Estado', {
            'fields': ('esta_de_baja', 'fecha_baja', 'observaciones')
        }),
        ('Tiempos', {
            'fields': ('fecha_creacion', 'ultima_modificacion')
        }),
    )
