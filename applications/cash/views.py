from django.db import models, transaction
from django.db.models import Sum, Count, F, Avg, ExpressionWrapper, FloatField
from django.views.generic import TemplateView, View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.utils.timezone import localdate
from datetime import timedelta
from applications.home.models import Venta, DetalleVenta
from .models import AperturaCaja
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

    def get(self, request, *args, **kwargs):
        apertura = self._apertura_hoy(request.user)
        form = AperturaCajaForm()
        
        # Buscar últimos cierres para recuperar
        from applications.cash.models import CierreCaja
        
        # Buscar el último cierre (de cualquier fecha)
        ultimo_cierre = CierreCaja.objects.order_by('-hora_cierre').first()
        
        # También buscar cierres recientes (últimos 7 días)
        from datetime import timedelta
        hace_7_dias = localdate() - timedelta(days=7)
        cierres_recientes = CierreCaja.objects.filter(
            fecha__gte=hace_7_dias
        ).order_by('-fecha', '-hora_cierre')[:5]
        
        return render(request, self.template_name, {
            "form": form,
            "apertura_activa": apertura,
            "ultimo_cierre": ultimo_cierre,
            "cierres_recientes": cierres_recientes,
        })

    def post(self, request, *args, **kwargs):
        # Si ya tiene una apertura abierta, no permitir duplicar
        apertura = self._apertura_hoy(request.user)
        if apertura:
            messages.warning(request, "Ya existe una apertura de caja abierta para hoy.")
            return redirect("home_app:tpv_general")

        # Ver si viene del botón de recuperar cierre (campo oculto)
        fondo_recuperado = request.POST.get('fondo_inicial')
        
        if fondo_recuperado:
            # Crear apertura directamente con el valor recuperado
            from decimal import Decimal
            try:
                fondo_val = Decimal(fondo_recuperado)
                AperturaCaja.objects.create(
                    usuario=request.user,
                    fecha=localdate(),
                    fondo_inicial=fondo_val,
                    estado='abierta'
                )
                messages.success(request, f"Caja abierta con fondo recuperado de {fondo_val} €")
                return redirect("home_app:tpv_general")
            except Exception as e:
                messages.error(request, f"Error al recuperar fondo: {e}")
        
        form = AperturaCajaForm(request.POST)
        if form.is_valid():
            ap = form.save(commit=False)
            ap.usuario = request.user
            ap.fecha = localdate()
            ap.save()
            messages.success(request, f"Caja abierta con fondo inicial de {ap.fondo_inicial} €")
            return redirect("home_app:tpv_general")

        return render(request, self.template_name, {
            "form": form,
            "apertura_activa": None,
        })