from django.contrib import admin
from .models import Punch
from django.utils.html import format_html

@admin.register(Punch)
class PunchAdmin(admin.ModelAdmin):
    list_display = (
        'get_user_fullname',
        'get_punch_code',
        'clock_in',
        'clock_out',
        'get_nif',
        'get_telefono',
    )
    list_filter = ('employee', 'clock_in', 'clock_out')
    search_fields = ('employee__user__first_name', 'employee__user__last_name', 'employee__nif')

    @admin.display(ordering='employee__user__last_name', description='Nombre')
    def get_user_fullname(self, obj):
        return obj.employee.user.get_full_name()

    @admin.display(description='Código de fichaje')
    def get_punch_code(self, obj):
        return obj.employee.punch_code

    @admin.display(description='NIF')
    def get_nif(self, obj):
        return obj.employee.nif

    @admin.display(description='Teléfono')
    def get_telefono(self, obj):
        return obj.employee.telefono
