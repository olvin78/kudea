from django.db import models, transaction
from django.db.models import Sum, Count, F, Avg, ExpressionWrapper, FloatField
from django.views.generic import TemplateView, View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.utils.timezone import localdate
from datetime import timedelta
from applications.home.models import Venta, DetalleVenta
from .models import AperturaCaja, Caja
from .forms import AperturaCajaForm


# ============================================================
# ==================== VISTA PRINCIPAL =======================
# ============================================================

class CashIndexView(TemplateView):

    template_name = "cash/index.html"


    # ============================================================
    # ==================== CONTEXTO PRINCIPAL ====================
    # ============================================================

    def get_context_data(self, **kwargs):

        context = super().get_context_data(**kwargs)

        # ============================================================
        # ==================== FECHA LOCAL CORRECTA ==================
        # ============================================================

        hoy = localdate()

        # Estado de apertura de caja
        apertura_activa = AperturaCaja.objects.filter(
            usuario=self.request.user,
            fecha=hoy,
            estado="abierta"
        ).first()

        # Periodo seleccionado desde botones (GET)
        periodo = self.request.GET.get("periodo", "hoy")


        # ============================================================
        # ==================== 1️⃣ KPI SUPERIOR ======================
        # ========== SIEMPRE SOLO VENTAS DEL DÍA ACTUAL =============
        # ============================================================

        ventas_hoy = Venta.objects.filter(
            creado_en__date=hoy,
            estado="completada"
        )

        total_hoy = ventas_hoy.aggregate(
            total=Sum("total")
        )["total"] or 0

        # Comparativa vs Ayer
        ayer = hoy - timedelta(days=1)
        total_ayer = Venta.objects.filter(
            creado_en__date=ayer,
            estado="completada"
        ).aggregate(total=Sum("total"))["total"] or 0
        
        crecimiento = 0
        if total_ayer > 0:
            crecimiento = ((total_hoy - total_ayer) / total_ayer) * 100

        tickets_hoy = ventas_hoy.count()
        ticket_medio = total_hoy / tickets_hoy if tickets_hoy > 0 else 0

        productos_hoy = DetalleVenta.objects.filter(
            venta__in=ventas_hoy
        ).aggregate(
            cantidad=Sum("cantidad")
        )["cantidad"] or 0

        context["kpi_hoy"] = {
            "total": total_hoy,
            "total_ayer": total_ayer,
            "crecimiento": crecimiento,
            "tickets": tickets_hoy,
            "productos": productos_hoy,
            "ticket_medio": ticket_medio,
        }


        # ============================================================
        # ==================== 2️⃣ ALERTAS Y RECAUDACIÓN =============
        # ============================================================

        # Desglose de Cobros Hoy (Reconciliación)
        context["recaudacion_hoy"] = ventas_hoy.values(
            "metodo_pago__nombre"
        ).annotate(
            total=Sum("total")
        ).order_by("-total")

        # Alertas de Stock (Críticas)
        from applications.product.models import Producto
        context["alertas_stock"] = Producto.objects.filter(
            activo=True,
            stock__lt=models.F('stock_minimo')
        ).order_by('stock')[:6]


        # ============================================================
        # ==================== 3️⃣ FILTRO INFERIOR ===================
        # ========== PARA LISTADO Y MÉTODOS DE PAGO =================
        # ============================================================

        # Definimos rango de fechas según botón

        if periodo == "ayer":
            fecha_inicio = hoy - timedelta(days=1)
            fecha_fin = fecha_inicio

        elif periodo == "semana":
            fecha_inicio = hoy - timedelta(days=7)
            fecha_fin = hoy

        elif periodo == "mes":
            fecha_inicio = hoy.replace(day=1)
            fecha_fin = hoy

        else:  # Por defecto = hoy
            fecha_inicio = hoy
            fecha_fin = hoy


        # Query principal para el periodo seleccionado
        ventas_periodo = Venta.objects.filter(
            creado_en__date__range=(fecha_inicio, fecha_fin),
            estado="completada"
        )


        # ============================================================
        # ==================== 3️⃣ VENTAS RECIENTES ==================
        # ============================================================

        context["ventas_recientes"] = ventas_periodo.order_by("-creado_en")


        # ============================================================
        # ==================== 4️⃣ MÉTODOS DE PAGO ===================
        # ============================================================

        context["totales_metodo"] = ventas_periodo.values(
            "metodo_pago__nombre"
        ).annotate(
            total=Sum("total")
        )


        # ============================================================
        # ==================== 5️⃣ PERIODO ACTUAL ====================
        # ============================================================

        context["apertura_hoy"] = apertura_activa
        context["periodo_actual"] = periodo

        return context


# ============================================================
#  Vista de Apertura de Caja
# ============================================================

class AperturaCajaView(LoginRequiredMixin, View):
    """
    Permite al cajero registrar el fondo inicial al abrir la caja.
    Si ya existe una apertura abierta para hoy, redirige al TPV.
    """
    template_name = "cash/apertura_caja.html"

    def _apertura_hoy(self, user):
        return AperturaCaja.objects.filter(
            usuario=user,
            fecha=localdate(),
            estado="abierta"
        ).first()

    def _apertura_pausada(self, user):
        return AperturaCaja.objects.filter(
            usuario=user,
            estado="pausada"
        ).first()

    def _cierres_por_caja(self):
        from applications.cash.models import CierreCaja
        cierres = {}
        for c in Caja.objects.filter(activa=True):
            ultimo = CierreCaja.objects.filter(caja=c).order_by('-hora_cierre').first()
            if ultimo:
                cierres[c.id] = ultimo
        return cierres

    def _get_moneda(self):
        from applications.home.models import ConfiguracionTPV
        cfg = ConfiguracionTPV.objects.first()
        moneda = (cfg.moneda if cfg else "C$") or "C$"
        return "C$" if moneda in {"", "€", "ARS"} else moneda

    def get(self, request, *args, **kwargs):
        apertura = self._apertura_hoy(request.user)
        apertura_pausada = self._apertura_pausada(request.user)
        from applications.config.models import ConfiguracionFiscal
        cfg_fiscal = ConfiguracionFiscal.objects.first()
        if apertura_pausada:
            fondo_defecto = float(apertura_pausada.fondo_inicial)
        else:
            fondo_defecto = cfg_fiscal.fondo_caja_defecto if cfg_fiscal else 200
        form = AperturaCajaForm(initial={'fondo_inicial': fondo_defecto})
        
        cajas_disponibles = Caja.objects.filter(activa=True)
        cierres_por_caja = self._cierres_por_caja()

        import json
        from django.utils.dateformat import format as date_format
        cierres_json = {}
        for cid, cierre in cierres_por_caja.items():
            cierres_json[str(cid)] = {
                'fecha': date_format(cierre.fecha, 'd/m/Y'),
                'monto': str(cierre.efectivo_retirado),
            }

        # Últimos 7 días de cierres para cada caja
        from applications.cash.models import CierreCaja
        from datetime import timedelta
        hace_7_dias = localdate() - timedelta(days=7)
        cierres_recientes = CierreCaja.objects.filter(
            fecha__gte=hace_7_dias
        ).order_by('-fecha', '-hora_cierre')[:5]

        return render(request, self.template_name, {
            "form": form,
            "apertura_activa": apertura,
            "apertura_pausada": apertura_pausada,
            "cierres_por_caja": cierres_por_caja,
            "cierres_json": json.dumps(cierres_json, ensure_ascii=False),
            "cierres_recientes": cierres_recientes,
            "moneda": self._get_moneda(),
            "cajas": cajas_disponibles,
        })

    def post(self, request, *args, **kwargs):
        # Si ya tiene una apertura abierta, no permitir duplicar
        apertura = self._apertura_hoy(request.user)
        if apertura:
            messages.warning(request, "Ya existe una apertura de caja abierta para hoy.")
            return redirect("home_app:tpv_general")

        caja_id = request.POST.get('caja_id', '')
        caja = None
        if caja_id:
            caja = Caja.objects.filter(id=caja_id, activa=True).first()

        if not caja:
            messages.error(request, "Selecciona una caja válida.")
            return redirect("cash_app:apertura_caja")

        # Bloquear si la caja ya tiene una apertura abierta o pausada por OTRO usuario
        apertura_existente = AperturaCaja.objects.filter(
            caja=caja,
            estado__in=['abierta', 'pausada']
        ).exclude(usuario=request.user).first()
        if apertura_existente:
            estado_txt = "abierta" if apertura_existente.estado == "abierta" else "en pausa"
            messages.error(request, f"La caja '{caja.nombre}' ya está {estado_txt} por {apertura_existente.usuario.username}. No puedes abrirla hasta que se cierre.")
            return redirect("cash_app:apertura_caja")

        # Reanudar si el mismo usuario tiene una apertura pausada en esta caja
        apertura_pausada = AperturaCaja.objects.filter(
            usuario=request.user,
            caja=caja,
            estado="pausada"
        ).first()
        if apertura_pausada:
            # Validar PIN también para reanudar
            pin_correcto = caja.pin if caja.pin else "1234"
            pin_usuario = request.POST.get('pin_apertura', '').strip()
            if pin_usuario != pin_correcto:
                messages.error(request, f"PIN incorrecto para reanudar '{caja.nombre}'.")
                return redirect("cash_app:apertura_caja")
            apertura_pausada.estado = "abierta"
            apertura_pausada.save()
            messages.success(request, f"Turno reanudado en '{caja.nombre}'.")
            return redirect("home_app:tpv_general")

        # Validar PIN contra la caja seleccionada
        pin_correcto = caja.pin if caja.pin else "1234"
        pin_usuario = request.POST.get('pin_apertura', '').strip()
        if pin_usuario != pin_correcto:
            messages.error(request, f"El PIN de seguridad para '{caja.nombre}' es incorrecto.")
            
            form = AperturaCajaForm(request.POST)
            ctx = self._build_error_context(request)
            ctx.update({"form": form, "apertura_activa": None, "apertura_pausada": None})
            return render(request, self.template_name, ctx)
        
        form = AperturaCajaForm(request.POST)
        if form.is_valid():
            ap = form.save(commit=False)
            ap.usuario = request.user
            ap.fecha = localdate()
            ap.caja = caja
            ap.save()
            from applications.home.models import ConfiguracionTPV
            moneda = ConfiguracionTPV.objects.first().moneda if ConfiguracionTPV.objects.exists() else "C$"
            messages.success(request, f"Caja '{caja.nombre}' abierta con fondo inicial de {ap.fondo_inicial} {moneda}")
            return redirect("home_app:tpv_general")

        # Si el form no es válido
        ctx = self._build_error_context(request)
        ctx.update({"form": form, "apertura_activa": None, "apertura_pausada": None})
        return render(request, self.template_name, ctx)

    def _build_error_context(self, request):
        from applications.cash.models import CierreCaja
        import json
        from django.utils.dateformat import format as date_format
        from datetime import timedelta
        cajas_disponibles = Caja.objects.filter(activa=True)
        cierres_por_caja = self._cierres_por_caja()
        cierres_json = {}
        for cid, cierre in cierres_por_caja.items():
            cierres_json[str(cid)] = {
                'fecha': date_format(cierre.fecha, 'd/m/Y'),
                'monto': str(cierre.efectivo_retirado),
            }
        hace_7_dias = localdate() - timedelta(days=7)
        cierres_recientes = CierreCaja.objects.filter(
            fecha__gte=hace_7_dias
        ).order_by('-fecha', '-hora_cierre')[:5]
        return {
            "cierres_por_caja": cierres_por_caja,
            "cierres_json": json.dumps(cierres_json, ensure_ascii=False),
            "cierres_recientes": cierres_recientes,
            "moneda": self._get_moneda(),
            "cajas": cajas_disponibles,
        }


class PauseCajaView(LoginRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        apertura = AperturaCaja.objects.filter(
            usuario=request.user,
            estado="abierta"
        ).first()
        if not apertura:
            messages.error(request, "No tienes ninguna caja abierta para pausar.")
            return redirect("home_app:tpv_general")
        apertura.estado = "pausada"
        apertura.save()
        caja_nombre = apertura.caja.nombre if apertura.caja else "Caja"
        messages.success(request, f"'{caja_nombre}' pausada. Vuelve a abrir caja para reanudar.")
        return redirect("cash_app:apertura_caja")
