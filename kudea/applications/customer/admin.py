from django.contrib import admin
from applications.customer.models import Cliente

@admin.register(Cliente)
class ClienteAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'correo', 'telefono']
