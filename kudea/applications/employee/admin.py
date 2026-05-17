from django.contrib import admin
from django.utils.html import format_html
from django.contrib.auth.models import User
from .models import Employee
import qrcode
import io
import base64

@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):
    list_display = (
        'user',
        'usuario',
        'codigo',
        'nif',
        'telefono',
        'es_administrador',
        'esta_de_baja',
        'ultima_modificacion',
        'show_qr'
    )

    readonly_fields = (
        'user_info',
        'codigo',
        'qr_token',
        'show_qr',
        'fecha_creacion',
        'ultima_modificacion',
    )


    fieldsets = (
        ('Usuario', {
            'fields': ('user', 'user_info')
        }),
        ('Identificación', {
            'fields': ('usuario', 'codigo', 'qr_token', 'show_qr')
        }),
        ('Datos personales', {
            'fields': ('nombre', 'apellidos', 'nif', 'telefono', 'movil', 'direccion', 'cp', 'poblacion', 'provincia')
        }),
        ('Permisos', {
            'fields': (
                'es_administrador',
                'puede_realizar_salidas',
                'puede_cambiar_fecha_hora',
                'puede_modificar_ventas',
                'puede_cambiar_subtotales',
                'puede_cambiar_tarifa'
            )
        }),
        ('Estado', {
            'fields': ('esta_de_baja', 'fecha_baja', 'observaciones')
        }),
        ('Auditoría', {
            'fields': ('fecha_creacion', 'ultima_modificacion')
        }),
    )

    def user_info(self, obj):
        return format_html(
            "<strong>{}</strong><br><small>{}</small><br><code>{}</code>",
            obj.user.get_full_name(),
            obj.user.email,
            obj.user.username
        )
    user_info.short_description = "Información del Usuario"

    def show_qr(self, obj):
        if not obj.qr_token:
            return "No QR"
        url = f"http://localhost:8000/attendance/fichar/{obj.qr_token}/"
        qr = qrcode.make(url)
        buffer = io.BytesIO()
        qr.save(buffer)
        img_str = base64.b64encode(buffer.getvalue()).decode()
        return format_html(f'<img src="data:image/png;base64,{img_str}" width="120" />')
    show_qr.short_description = "QR Code"
