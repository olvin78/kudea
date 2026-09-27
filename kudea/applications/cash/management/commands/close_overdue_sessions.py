from django.core.management.base import BaseCommand
from django.utils import timezone
from applications.cash.models import AperturaCaja, CierreCaja


class Command(BaseCommand):
    help = 'Cierra automáticamente las cajas que se quedaron abiertas de días anteriores.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--con-cierre',
            action='store_true',
            help='Solo cierra sesiones que ya tengan un CierreCaja que las cubra.',
        )

    def handle(self, *args, **options):
        hoy = timezone.localdate()
        pendientes = AperturaCaja.objects.filter(
            estado__in=['abierta', 'pausada'],
            fecha__lt=hoy,
        ).select_related('usuario', 'caja')

        if not pendientes.exists():
            self.stdout.write(self.style.SUCCESS('No hay cajas pendientes de días anteriores.'))
            return

        cerradas = 0
        sin_arqueo = 0

        for sesion in pendientes:
            cubierta = CierreCaja.objects.filter(
                fecha_inicio__lte=sesion.fecha,
                fecha_fin__gte=sesion.fecha,
                caja=sesion.caja,
            ).exists()

            if options['con_cierre'] and not cubierta:
                sin_arqueo += 1
                continue

            self.stdout.write(
                f"Cerrando caja de {sesion.usuario.username} del día {sesion.fecha} "
                f"(abierta desde {sesion.hora_apertura:%d/%m/%Y %H:%M})..."
            )
            sesion.estado = 'cerrada'
            sesion.hora_cierre = timezone.now()
            sesion.save(update_fields=['estado', 'hora_cierre'])
            cerradas += 1
            if not cubierta:
                self.stdout.write(self.style.WARNING(
                    f"  Aviso: el {sesion.fecha:%d/%m/%Y} de {sesion.usuario.username} "
                    f"no tenía arqueo (CierreCaja) registrado."
                ))

        if cerradas:
            self.stdout.write(self.style.SUCCESS(f'{cerradas} caja(s) cerrada(s).'))
        if sin_arqueo:
            self.stdout.write(self.style.WARNING(
                f'{sin_arqueo} caja(s) siguen abiertas porque su día no tiene arqueo.'
            ))
