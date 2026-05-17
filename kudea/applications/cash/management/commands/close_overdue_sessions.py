from django.core.management.base import BaseCommand
from django.utils import timezone
from applications.cash.models import AperturaCaja
from applications.home.views import registrar_cierre_desde_rango
from django.contrib.auth.models import User

class Command(BaseCommand):
    help = 'Cierra automáticamente las cajas que se quedaron abiertas de días anteriores.'

    def handle(self, *args, **options):
        hoy = timezone.localdate()
        cajas_pendientes = AperturaCaja.objects.filter(estado='abierta', fecha__lt=hoy)
        
        if not cajas_pendientes.exists():
            self.stdout.write(self.style.SUCCESS('No hay cajas pendientes de días anteriores.'))
            return

        # Usar un usuario administrador para el registro del cierre automático
        admin_user = User.objects.filter(is_superuser=True).first()
        
        for caja in cajas_pendientes:
            self.stdout.write(f"Cerrando caja de {caja.usuario.username} del día {caja.fecha}...")
            
            # Simulamos un request básico para la función de registro
            class MockRequest:
                def __init__(self, user):
                    self.user = user
                    self._messages = []
            
            mock_request = MockRequest(admin_user)
            
            try:
                registrar_cierre_desde_rango(mock_request, "diario", caja.fecha, caja.fecha)
                self.stdout.write(self.style.SUCCESS(f"Caja del {caja.fecha} cerrada correctamente."))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"Error al cerrar caja del {caja.fecha}: {str(e)}"))
