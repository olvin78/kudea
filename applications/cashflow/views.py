from datetime import timedelta
from decimal import Decimal

from django.utils import timezone
from django.views.generic import ListView, DetailView
from django.db.models import Sum
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_protect
from django.contrib.auth.decorators import login_required

from .models import Movimiento, Cuenta
from .services import register_movement


# ============================================================
# UTILIDAD RANGO FECHAS
# ============================================================

def get_date_range(request):
    periodo = request.GET.get("periodo", "hoy")
    now = timezone.localtime()

    start = end = None

    if periodo == "hoy":
        start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        end = start + timedelta(days=1)

    elif periodo == "semana":
        start = (now - timedelta(days=now.weekday())).replace(
            hour=0, minute=0, second=0, microsecond=0
        )
        end = start + timedelta(days=7)

    elif periodo == "mes":
        start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        if start.month == 12:
            end = start.replace(year=start.year + 1, month=1)
        else:
            end = start.replace(month=start.month + 1)

    elif periodo == "anio":
        start = now.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
        end = start.replace(year=start.year + 1)

    elif periodo == "custom":
        start_str = request.GET.get("start_date")
        end_str = request.GET.get("end_date")
        try:
            if start_str:
                start = timezone.datetime.strptime(start_str, "%Y-%m-%d")
                start = timezone.make_aware(start).replace(hour=0, minute=0, second=0)
            if end_str:
                end = timezone.datetime.strptime(end_str, "%Y-%m-%d")
                end = timezone.make_aware(end).replace(hour=23, minute=59, second=59)
        except ValueError:
            pass

    return periodo, start, end


# ============================================================
# LISTADO PRINCIPAL CASHFLOW
# ============================================================

class CashflowListView(ListView):
    model = Movimiento
    template_name = "cashflow/movement_list.html"
    context_object_name = "movimientos"
    paginate_by = 50

    def get_queryset(self):
        qs = super().get_queryset().select_related("cuenta")

        self.periodo, start, end = get_date_range(self.request)

        if start:
            qs = qs.filter(fecha__gte=start)
        if end:
            qs = qs.filter(fecha__lt=end)

        cuenta_id = self.request.GET.get("cuenta")
        if cuenta_id:
            qs = qs.filter(cuenta_id=cuenta_id)

        origen = self.request.GET.get("origen")
        if origen:
            qs = qs.filter(origen=origen)

        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # ⚠️ IMPORTANTE: usar queryset sin paginar para totales
        qs = self.get_queryset()
        now = timezone.localtime()
        
        # --- TOTALES BASE ---
        entradas = qs.filter(tipo=Movimiento.Tipo.INGRESO).aggregate(total=Sum("cantidad"))["total"] or Decimal("0.00")
        salidas = qs.filter(tipo=Movimiento.Tipo.GASTO).aggregate(total=Sum("cantidad"))["total"] or Decimal("0.00")
        ajustes = qs.filter(tipo=Movimiento.Tipo.AJUSTE).aggregate(total=Sum("cantidad"))["total"] or Decimal("0.00")
        
        salidas_total = salidas + ajustes
        saldo = entradas - salidas_total

        # --- KPIs DASHBOARD (MES ACTUAL vs ANTERIOR) ---
        start_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        
        # Ingresos/Gastos Mes Actual
        movs_mes = Movimiento.objects.filter(fecha__gte=start_month)
        ingresos_mes = movs_mes.filter(tipo=Movimiento.Tipo.INGRESO).aggregate(total=Sum("cantidad"))["total"] or Decimal("0.00")
        gastos_mes = movs_mes.filter(tipo=Movimiento.Tipo.GASTO).aggregate(total=Sum("cantidad"))["total"] or Decimal("0.00")

        # Mes Anterior
        last_month = start_month - timedelta(days=1)
        start_last_month = last_month.replace(day=1)
        end_last_month = start_month
        
        movs_last_month = Movimiento.objects.filter(fecha__gte=start_last_month, fecha__lt=end_last_month)
        ingresos_last_month = movs_last_month.filter(tipo=Movimiento.Tipo.INGRESO).aggregate(total=Sum("cantidad"))["total"] or Decimal("1.00") # Evitar div por cero
        
        # Crecimiento
        growth = ((ingresos_mes - ingresos_last_month) / ingresos_last_month * 100) if ingresos_last_month > 0 else 0

        # --- CHART DATA 1: Distribución Gastos (Categoría/Canal) ---
        from django.db.models import Count
        gastos_dist = movs_mes.filter(tipo=Movimiento.Tipo.GASTO).values('canal_operacion').annotate(total=Sum('cantidad')).order_by('-total')
        
        chart_donut_labels = [dict(Movimiento.CanalOperacion.choices).get(g['canal_operacion'], g['canal_operacion']) for g in gastos_dist]
        chart_donut_data = [float(g['total']) for g in gastos_dist]

        # --- CHART DATA 2: Ingresos vs Gastos Semanal ---
        from django.db.models.functions import TruncDay
        last_7_days = now - timedelta(days=7)
        weekly_stats = Movimiento.objects.filter(fecha__gte=last_7_days).annotate(day=TruncDay('fecha')).values('day', 'tipo').annotate(total=Sum('cantidad')).order_by('day')
        
        # Organizar datos para Chart.js
        days_labels = []
        ingresos_weekly = {}
        gastos_weekly = {}
        
        for i in range(7):
            d = (last_7_days + timedelta(days=i+1)).date()
            d_str = d.strftime('%d %b')
            days_labels.append(d_str)
            ingresos_weekly[d] = 0
            gastos_weekly[d] = 0
            
        for s in weekly_stats:
            d = s['day'].date()
            if d in ingresos_weekly:
                if s['tipo'] == 'ingreso':
                    ingresos_weekly[d] = float(s['total'] or 0)
                elif s['tipo'] == 'gasto':
                    gastos_weekly[d] = float(s['total'] or 0)

        chart_bar_labels = days_labels
        chart_bar_ingresos = [ingresos_weekly[d] for d in sorted(ingresos_weekly.keys())]
        chart_bar_gastos = [gastos_weekly[d] for d in sorted(gastos_weekly.keys())]

        # --- CIERRES DE CAJA ---
        from applications.cash.models import CierreCaja
        ultimos_cierres = CierreCaja.objects.all().order_by('-fecha_fin')[:5]

        # --- RENDIMIENTO POR USUARIO ---
        from applications.home.models import Venta
        from django.contrib.auth.models import User
        user_performance = User.objects.annotate(
            total_ventas=Sum('venta__total')
        ).filter(total_ventas__gt=0).order_by('-total_ventas')[:5]

        # --- CAJAS ABIERTAS ACTUALMENTE ---
        from applications.cash.models import AperturaCaja
        cajas_abiertas = AperturaCaja.objects.filter(estado='abierta').select_related('usuario')

        context.update({
            "entradas_total": entradas,
            "salidas_total": salidas_total,
            "saldo_total": saldo,
            "periodo": getattr(self, "periodo", "hoy"),
            "hoy": now.date(),
            "cuentas": Cuenta.objects.filter(activa=True),
            "ingresos_mes": ingresos_mes,
            "gastos_mes": gastos_mes,
            "growth": growth,
            "chart_donut_labels": chart_donut_labels,
            "chart_donut_data": chart_donut_data,
            "chart_bar_labels": chart_bar_labels,
            "chart_bar_ingresos": chart_bar_ingresos,
            "chart_bar_gastos": chart_bar_gastos,
            "ultimos_cierres": ultimos_cierres,
            "user_performance": user_performance,
            "canales": Movimiento.CanalOperacion.choices,
            "cajas_abiertas": cajas_abiertas,
        })

        return context


# ============================================================
# CREAR MOVIMIENTO VIA MODAL (AJAX)
# ============================================================

@require_POST
@csrf_protect
@login_required
def crear_movimiento_ajax(request):
    try:
        concepto = request.POST.get("concepto")
        tipo = request.POST.get("tipo")
        cuenta_id = request.POST.get("cuenta")
        cantidad = request.POST.get("cantidad")
        canal_operacion = request.POST.get("canal_operacion", Movimiento.CanalOperacion.DIRECTA)

        if not all([concepto, tipo, cuenta_id, cantidad]):
            return JsonResponse(
                {"success": False, "error": "Datos incompletos"},
                status=400
            )

        cuenta = Cuenta.objects.get(id=cuenta_id)

        register_movement(
            concepto=concepto,
            tipo=tipo,
            origen=Movimiento.Origen.MANUAL,
            cuenta=cuenta,
            cantidad=Decimal(cantidad),
            created_by=request.user,
            canal_operacion=canal_operacion,
        )

        return JsonResponse({"success": True})

    except Cuenta.DoesNotExist:
        return JsonResponse(
            {"success": False, "error": "Cuenta inválida"},
            status=400
        )

    except Exception as e:
        return JsonResponse(
            {"success": False, "error": str(e)},
            status=400
        )


# ============================================================
# DETALLE DE MOVIMIENTO (AJAX) - PARA EL MODAL
# ============================================================

def detalle_movimiento_api(request, movimiento_id):
    """
    Endpoint para obtener los detalles de un movimiento específico
    para mostrarlos en el modal rápido
    """
    try:
        movimiento = Movimiento.objects.select_related('cuenta', 'created_by').get(id=movimiento_id)

        # Determinar el método de pago (si existe en tu modelo)
        metodo_pago = "No especificado"
        if hasattr(movimiento, 'metodo_pago') and movimiento.metodo_pago:
            metodo_pago = movimiento.metodo_pago

        # Notas (si existen)
        notas = ""
        if hasattr(movimiento, 'notas') and movimiento.notas:
            notas = movimiento.notas

        # Creado por
        creado_por = "Sistema"
        if movimiento.created_by:
            creado_por = movimiento.created_by.username

        return JsonResponse({
            'success': True,
            'movimiento': {
                'id': movimiento.id,
                'fecha': movimiento.fecha.strftime('%d/%m/%Y %H:%M'),
                'concepto': movimiento.concepto,
                'tipo': movimiento.tipo,
                'tipo_display': movimiento.get_tipo_display(),
                'cantidad': float(movimiento.cantidad),
                'cuenta': movimiento.cuenta.nombre,
                'metodo_pago': metodo_pago,
                'creado_por': creado_por,
                'notas': notas
            }
        })
    except Movimiento.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Movimiento no encontrado'
        }, status=404)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


# ============================================================
# DETALLE COMPLETO DE MOVIMIENTO (PÁGINA TIPO FACTURA)
# ============================================================

class MovimientoDetailView(DetailView):
    """
    Vista para mostrar el detalle completo de un movimiento
    en formato tipo factura / comprobante
    """
    model = Movimiento
    template_name = "cashflow/movimiento_detalle_completo.html"
    context_object_name = "movimiento"
    pk_url_kwarg = 'pk'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        movimiento = self.get_object()

        # Formatear fecha para mostrarla bonita
        context['fecha_formateada'] = movimiento.fecha.strftime('%d/%m/%Y')
        context['hora_formateada'] = movimiento.fecha.strftime('%H:%M')

        # Determinar el método de pago (si existe)
        if hasattr(movimiento, 'metodo_pago') and movimiento.metodo_pago:
            if hasattr(movimiento, 'get_metodo_pago_display'):
                context['metodo_pago'] = movimiento.get_metodo_pago_display()
            else:
                context['metodo_pago'] = movimiento.metodo_pago
        else:
            context['metodo_pago'] = 'No especificado'

        # Obtener usuario que creó
        context['creado_por'] = movimiento.created_by.username if movimiento.created_by else 'Sistema'

        return context