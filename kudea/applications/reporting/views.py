# =====================================================================
# 📁 VISTAS · APP 'reporting' — Dashboard, contabilidad (libro IVA) y exportes — SOLO LEE datos
# =====================================================================
#   L19    class DashboardPrincipalView(TemplateView):
# =====================================================================

from django.views.generic import TemplateView
from django.utils.timezone import localdate
from django.db import models
from django.db.models import Sum, F, Count, ExpressionWrapper
from django.db.models.functions import ExtractHour
from django.urls import reverse
from datetime import timedelta

from applications.home.models import Venta, DetalleVenta, Devolucion, DevolucionItem
from applications.product.models import Producto
from applications.config.models import ConfiguracionFiscal
from applications.customer.models import PagoFiado
from applications.purchases.models import Compra as CompraProveedor

# Paleta para los donuts (misma gama KUDEA)
COLORES_DONUT = ["#1D3557", "#457B9D", "#2A9D8F", "#F4A261", "#E63946", "#A8DADC", "#76C7BD", "#94A3B8"]


class DashboardPrincipalView(TemplateView):
    template_name = "reporting/dashboard.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        hoy = localdate()
        inicio_mes = hoy.replace(day=1)
        inicio_anio = hoy.replace(month=1, day=1)

        # =====================================================
        # 🔥 FILTROS TEMPORALES (V4)
        # =====================================================
        rango = self.request.GET.get('rango', 'hoy')
        f_inicio_str = self.request.GET.get('fecha_inicio')
        f_fin_str = self.request.GET.get('fecha_fin')

        f_filtro_inicio = hoy
        f_filtro_fin = hoy

        if rango == 'ayer':
            f_filtro_inicio = hoy - timedelta(days=1)
            f_filtro_fin = f_filtro_inicio
        elif rango == 'semana':
            f_filtro_inicio = hoy - timedelta(days=6)
            f_filtro_fin = hoy
        elif rango == 'mes':
            f_filtro_inicio = inicio_mes
            f_filtro_fin = hoy
        elif rango == 'anio':
            f_filtro_inicio = inicio_anio
            f_filtro_fin = hoy
        elif rango == 'personalizado' and f_inicio_str and f_fin_str:
            try:
                from datetime import datetime
                f_filtro_inicio = datetime.strptime(f_inicio_str, '%Y-%m-%d').date()
                f_filtro_fin = datetime.strptime(f_fin_str, '%Y-%m-%d').date()
            except ValueError:
                rango = 'hoy' # Fallback if dates are invalid
        else:
            rango = 'hoy'

        # =====================================================
        # 🔥 IVA ACTUAL (AÑADIDO)
        # =====================================================
        config = ConfiguracionFiscal.objects.first()
        iva_actual = float(config.iva_general) if config else 21.0

        def _dev_coste(dev_qs):
            """Coste de compra de las unidades devueltas (vuelven a almacén)."""
            return float(
                DevolucionItem.objects.filter(devolucion__in=dev_qs).annotate(
                    c=ExpressionWrapper(F("cantidad") * F("detalle__producto__costo"), output_field=models.FloatField())
                ).aggregate(t=Sum("c"))["t"] or 0
            )

        # =========================
        # Ventas HOY / MES / AÑO
        # =========================
        ventas_hoy = Venta.objects.filter(creado_en__date=hoy, estado="completada")
        ventas_mes = Venta.objects.filter(creado_en__date__range=(inicio_mes, hoy), estado="completada")
        ventas_anio = Venta.objects.filter(creado_en__date__range=(inicio_anio, hoy), estado="completada")

        total_hoy = float(ventas_hoy.aggregate(total=Sum("total"))["total"] or 0)
        total_mes_actual = float(ventas_mes.aggregate(total=Sum("total"))["total"] or 0)
        total_anio_actual = float(ventas_anio.aggregate(total=Sum("total"))["total"] or 0)

        # Devoluciones (NC): los KPI se muestran NETOS de lo devuelto
        dev_hoy = Devolucion.objects.filter(creado_en__date=hoy)
        dev_mes = Devolucion.objects.filter(creado_en__date__range=(inicio_mes, hoy))
        dev_anio = Devolucion.objects.filter(creado_en__date__range=(inicio_anio, hoy))
        dev_hoy_t = float(dev_hoy.aggregate(t=Sum("total"))["t"] or 0)
        dev_mes_t = float(dev_mes.aggregate(t=Sum("total"))["t"] or 0)
        dev_anio_t = float(dev_anio.aggregate(t=Sum("total"))["t"] or 0)
        total_hoy = max(0.0, total_hoy - dev_hoy_t)
        total_mes_actual = max(0.0, total_mes_actual - dev_mes_t)
        total_anio_actual = max(0.0, total_anio_actual - dev_anio_t)
        dev_mes_coste = _dev_coste(dev_mes)

        tickets_hoy = ventas_hoy.count()
        tickets_mes = ventas_mes.count()

        ticket_promedio_hoy = (total_hoy / tickets_hoy) if tickets_hoy else 0
        ticket_promedio_mes = (total_mes_actual / tickets_mes) if tickets_mes else 0

        # =========================
        # Mes anterior + crecimiento
        # =========================
        ultimo_dia_mes_anterior = inicio_mes - timedelta(days=1)
        inicio_mes_anterior = ultimo_dia_mes_anterior.replace(day=1)

        ventas_mes_anterior = Venta.objects.filter(
            creado_en__date__range=(inicio_mes_anterior, ultimo_dia_mes_anterior),
            estado="completada"
        )
        total_mes_anterior = float(ventas_mes_anterior.aggregate(total=Sum("total"))["total"] or 0)
        total_mes_anterior = max(0.0, total_mes_anterior - float(
            Devolucion.objects.filter(creado_en__date__range=(inicio_mes_anterior, ultimo_dia_mes_anterior)).aggregate(t=Sum("total"))["t"] or 0
        ))

        crecimiento = 0
        if total_mes_anterior > 0:
            crecimiento = ((total_mes_actual - total_mes_anterior) / total_mes_anterior) * 100

        # =========================
        # 📊 METRICAS DEL PERIODO FILTRADO (V8)
        # =========================
        ventas_periodo = Venta.objects.filter(
            creado_en__date__range=(f_filtro_inicio, f_filtro_fin),
            estado="completada"
        )
        total_periodo = float(ventas_periodo.aggregate(total=Sum("total"))["total"] or 0)
        tickets_periodo = ventas_periodo.count()

        # Devoluciones (notas de crédito) del periodo → resto a ventas y coste
        devoluciones_periodo = Devolucion.objects.filter(
            creado_en__date__range=(f_filtro_inicio, f_filtro_fin)
        )
        total_devoluciones_periodo = float(
            devoluciones_periodo.aggregate(t=Sum("total"))["t"] or 0
        )
        if total_devoluciones_periodo:
            total_periodo = max(0.0, total_periodo - total_devoluciones_periodo)

        ticket_promedio_periodo = (total_periodo / tickets_periodo) if tickets_periodo else 0

        # Margen del periodo filtrado (Operaciones puras en float)
        detalles_periodo = DetalleVenta.objects.filter(venta__in=ventas_periodo).annotate(
            coste_item=ExpressionWrapper(F("cantidad") * F("producto__costo"), output_field=models.FloatField())
        )
        coste_total_periodo = float(detalles_periodo.aggregate(total=Sum("coste_item"))["total"] or 0)
        coste_total_periodo = max(0.0, coste_total_periodo - _dev_coste(devoluciones_periodo))

        # Beneficio = Total - IVA - Coste
        iva_periodo = total_periodo * (iva_actual / (100 + iva_actual))
        beneficio_periodo = total_periodo - iva_periodo - coste_total_periodo
        margen_periodo = (beneficio_periodo / total_periodo * 100) if total_periodo > 0 else 0

        # =========================
        # Coste / Beneficio / Margen (MES - Se mantiene para reporte mensual fijo)
        # =========================
        detalles_mes = DetalleVenta.objects.filter(venta__in=ventas_mes).annotate(
            coste_item=ExpressionWrapper(F("cantidad") * F("producto__costo"), output_field=models.FloatField())
        )
        coste_total_mes = float(detalles_mes.aggregate(total=Sum("coste_item"))["total"] or 0)
        coste_total_mes = max(0.0, coste_total_mes - dev_mes_coste)
        
        iva_mes = total_mes_actual * (iva_actual / (100 + iva_actual))
        beneficio_bruto = total_mes_actual - iva_mes - coste_total_mes
        margen = (beneficio_bruto / total_mes_actual * 100) if total_mes_actual > 0 else 0

        # =========================
        # 🔥 PERFORMANCE POR USUARIO (Filtrado V7)
        # =========================
        ventas_usuario = (
            Venta.objects.filter(
                creado_en__date__range=(f_filtro_inicio, f_filtro_fin),
                estado="completada"
            ).values("usuario__username")
            .annotate(total=Sum("total"), n=Count("id"))
            .order_by("-total")
        )

        # =========================
        # 🔥 ANÁLISIS PROFUNDO DE PRODUCTOS (Soul 2.0)
        # =========================
        productos_soul = DetalleVenta.objects.filter(
            venta__in=ventas_mes
        ).values(
            "producto__nombre", 
            "producto__costo", 
            "producto__precio",
            "producto__stock",
            "producto__stock_minimo"
        ).annotate(
            unidades_vendidas=Sum("cantidad"),
            total_ingreso=Sum("total"),
        ).annotate(
            total_costo=F("unidades_vendidas") * F("producto__costo"),
            total_beneficio=F("total_ingreso") - (F("unidades_vendidas") * F("producto__costo")),
            indice_ruptura=ExpressionWrapper(
                F("producto__stock") * 1.0 / F("producto__stock_minimo"),
                output_field=models.FloatField()
            )
        )
        
        for p in productos_soul:
            try:
                p['ruptura_porcentaje'] = min(float(p['indice_ruptura']) * 100, 100)
            except (ValueError, TypeError, ZeroDivisionError):
                p['ruptura_porcentaje'] = 0

        productos_ganancia = productos_soul.order_by("-total_beneficio")[:5]
        productos_perdida = productos_soul.filter(total_beneficio__lt=0).order_by("total_beneficio")[:5]
        productos_criticos = productos_soul.filter(
            producto__stock__lte=F("producto__stock_minimo")
        ).order_by("indice_ruptura")[:5]

        # =========================
        # 🔥 ECONOMÍA POR CATEGORÍA
        # =========================
        categoria_stats = DetalleVenta.objects.filter(
            venta__in=ventas_mes
        ).values("producto__categoria__nombre").annotate(
            total_ventas=Sum("total"),
            n_articulos=Count("id")
        ).order_by("-total_ventas")

        # =========================
        # Productos top (MES)
        # =========================
        productos_top = DetalleVenta.objects.filter(
            venta__in=ventas_mes
        ).values("producto__nombre").annotate(
            total_vendido=Sum("cantidad")
        ).order_by("-total_vendido")[:5]
        
        producto_top_uno = productos_top[0] if productos_top.exists() else None

        # =========================
        # 🔥 INTELIGENCIA DE NEGOCIO V3
        # =========================
        dias_mes = (hoy - inicio_mes).days + 1
        for p in productos_soul:
            unidades = float(p['unidades_vendidas'] or 0)
            p['velocidad_diaria'] = round(unidades / dias_mes, 2)
            if p['velocidad_diaria'] > 0:
                p['dias_inventario'] = int(float(p['producto__stock']) / p['velocidad_diaria'])
            else:
                p['dias_inventario'] = 999

        productos_con_venta_ids = DetalleVenta.objects.filter(venta__in=ventas_mes).values_list('producto_id', flat=True).distinct()
        stock_muerto = Producto.objects.filter(
            activo=True, 
            stock__gt=0
        ).exclude(id__in=productos_con_venta_ids).annotate(
            valor_estancado=F("stock") * F("costo")
        ).order_by("-valor_estancado")[:5]

        # Cementerio de stock: totales y peso relativo de cada producto (para las barras)
        stock_muerto = list(stock_muerto)
        stock_muerto_total = sum(float(p.valor_estancado or 0) for p in stock_muerto)
        sm_max = max((float(p.valor_estancado or 0) for p in stock_muerto), default=0)
        for p in stock_muerto:
            p.cuota_pct = round(float(p.valor_estancado or 0) / sm_max * 100, 1) if sm_max else 0

        valor_venta_potencial = Producto.objects.filter(activo=True).aggregate(
            total=Sum(F("stock") * F("precio"), output_field=models.FloatField())
        )["total"] or 0

        ticker_eventos = []
        agotados = Producto.objects.filter(activo=True, stock=0).order_by("-creado_en")[:2]
        for a in agotados:
            ticker_eventos.append({"tipo": "peligro", "texto": f"STOCK AGOTADO: {a.nombre}"})
        gran_venta = ventas_hoy.filter(total__gt=100).order_by("-total").first()
        if gran_venta:
            ticker_eventos.append({"tipo": "exito", "texto": f"GRAN VENTA: {gran_venta.total}€ (Ticket #{gran_venta.id})"})
        if producto_top_uno:
            ticker_eventos.append({"tipo": "info", "texto": f"TOP VENTAS: {producto_top_uno['producto__nombre']}"})

        recaudacion_filtrada = (
            Venta.objects.filter(
                creado_en__date__range=(f_filtro_inicio, f_filtro_fin),
                estado="completada"
            ).values("metodo_pago__nombre")
            .annotate(total=Sum("total"), n=Count("id"))
            .order_by("-total")
        )

        ultimas_ventas = Venta.objects.filter(estado="completada").order_by("-creado_en")[:8]

        productos_stock_bajo = Producto.objects.filter(
            activo=True,
            stock__lte=F("stock_minimo")
        ).order_by("stock")

        inventario = Producto.objects.filter(activo=True).annotate(
            valor_stock=F("stock") * F("costo")
        )
        valor_total_inventario = inventario.aggregate(total=Sum("valor_stock"))["total"] or 0
        total_productos_activos = Producto.objects.filter(activo=True).count()

        # Ventas últimos 30 días
        fecha_inicio_grafico = hoy - timedelta(days=29)
        ventas_por_dia = []
        dias_labels = []
        for i in range(30):
            dia = fecha_inicio_grafico + timedelta(days=i)
            total_dia = Venta.objects.filter(creado_en__date=dia, estado="completada").aggregate(total=Sum("total"))["total"] or 0
            ventas_por_dia.append(float(total_dia))
            dias_labels.append(dia.strftime("%d/%m"))

        # =========================
        # 🔥 AUDITORÍA DE EXCEPCIONES
        # =========================
        ventas_con_descuento = ventas_periodo.filter(descuento__gt=0)
        total_descuentos_periodo = float(ventas_con_descuento.aggregate(total=Sum("descuento"))["total"] or 0)
        
        excepciones_iva = []
        for v in ventas_periodo:
            try:
                sub = float(v.subtotal)
                iva_v = float(v.iva)
                if sub > 0:
                    ratio = round((iva_v / sub) * 100, 1)
                    if abs(ratio - iva_actual) > 0.5:
                        excepciones_iva.append({
                            'codigo': v.codigo,
                            'total': v.total,
                            'iva_aplicado': ratio,
                            'fecha': v.creado_en
                        })
            except: pass

        # =========================
        # 🔥 ESTADO DE SALUD DINÁMICO
        # =========================
        n_agotados = Producto.objects.filter(activo=True, stock=0).count()
        n_bajo_minimo = productos_stock_bajo.count() - n_agotados
        
        health_status = "OPTIMAL"
        health_color = "emerald"
        if n_agotados > 0:
            health_status = "CRITICAL"
            health_color = "rose"
        elif n_bajo_minimo > 0:
            health_status = "WARNING"
            health_color = "amber"

        # =========================
        # 📈 COMPARATIVA vs PERIODO ANTERIOR (misma duración, inmediatamente anterior)
        # =========================
        dur_dias = (f_filtro_fin - f_filtro_inicio).days + 1
        p_fin = f_filtro_inicio - timedelta(days=1)
        p_inicio = p_fin - timedelta(days=max(dur_dias - 1, 0))
        ventas_periodo_anterior = Venta.objects.filter(
            creado_en__date__range=(p_inicio, p_fin), estado="completada"
        )
        agg_anterior = ventas_periodo_anterior.aggregate(total=Sum("total"), n=Count("id"))
        total_anterior = float(agg_anterior["total"] or 0)
        dev_anterior_qs = Devolucion.objects.filter(creado_en__date__range=(p_inicio, p_fin))
        total_anterior = max(0.0, total_anterior - float(dev_anterior_qs.aggregate(t=Sum("total"))["t"] or 0))
        tickets_anterior = agg_anterior["n"] or 0
        ticket_promedio_anterior = (total_anterior / tickets_anterior) if tickets_anterior else 0.0

        detalles_anterior = DetalleVenta.objects.filter(venta__in=ventas_periodo_anterior).annotate(
            coste_item=ExpressionWrapper(F("cantidad") * F("producto__costo"), output_field=models.FloatField())
        )
        coste_anterior = float(detalles_anterior.aggregate(total=Sum("coste_item"))["total"] or 0)
        coste_anterior = max(0.0, coste_anterior - _dev_coste(dev_anterior_qs))
        iva_anterior = total_anterior * (iva_actual / (100 + iva_actual))
        beneficio_anterior = total_anterior - iva_anterior - coste_anterior
        margen_anterior = (beneficio_anterior / total_anterior * 100) if total_anterior > 0 else 0.0

        def _delta(actual, anterior):
            """% de variación vs periodo anterior; None si no hay base comparable."""
            if not anterior:
                return None
            return round(((actual - anterior) / abs(anterior)) * 100, 1)

        delta_periodo = _delta(total_periodo, total_anterior)
        delta_beneficio = _delta(beneficio_periodo, beneficio_anterior)
        delta_ticket = _delta(ticket_promedio_periodo, ticket_promedio_anterior)
        delta_margen_pp = (
            round(margen_periodo - margen_anterior, 1)
            if total_periodo > 0 and total_anterior > 0 else None
        )

        # =========================
        # 🍩 DONUTS: mix de ventas del periodo por método de pago y por categoría
        # =========================
        dev_por_metodo = {
            r["venta__metodo_pago__nombre"]: float(r["t"] or 0)
            for r in devoluciones_periodo.values("venta__metodo_pago__nombre").annotate(t=Sum("total"))
        }
        mix_pagos = []
        for r in ventas_periodo.values("metodo_pago__nombre").annotate(t=Sum("total")).order_by("-t"):
            nombre = r["metodo_pago__nombre"] or "Sin método"
            t = float(r["t"] or 0) - dev_por_metodo.get(nombre, 0)
            if t <= 0:
                continue
            mix_pagos.append({
                "nombre": nombre,
                "total": t,
                "pct": round(t / total_periodo * 100, 1) if total_periodo else 0,
                "color": COLORES_DONUT[len(mix_pagos) % len(COLORES_DONUT)],
            })

        dev_por_cat = {
            r["detalle__producto__categoria__nombre"]: float(r["t"] or 0)
            for r in DevolucionItem.objects.filter(devolucion__in=devoluciones_periodo).values(
                "detalle__producto__categoria__nombre"
            ).annotate(t=Sum("subtotal"))
        }
        mix_categorias = []
        filas_cat = DetalleVenta.objects.filter(venta__in=ventas_periodo).values(
            "producto__categoria__nombre"
        ).annotate(t=Sum("total")).order_by("-t")
        for r in filas_cat:
            nombre = r["producto__categoria__nombre"] or "Sin categoría"
            t = float(r["t"] or 0) - dev_por_cat.get(nombre, 0)
            if t <= 0:
                continue
            mix_categorias.append({
                "nombre": nombre,
                "total": t,
                "pct": 0,
                "color": COLORES_DONUT[len(mix_categorias) % len(COLORES_DONUT)],
            })
        total_categorias = float(sum(x["total"] for x in mix_categorias))
        for x in mix_categorias:
            x["pct"] = round(x["total"] / total_categorias * 100, 1) if total_categorias else 0

        # =========================
        # 💳 FIADO: pendiente total, vencido (+30 días) y antigüedad de la deuda
        # =========================
        pagos_por_venta = {
            r["venta_id"]: float(r["t"] or 0)
            for r in PagoFiado.objects.values("venta_id").annotate(t=Sum("cantidad"))
        }
        fiado_pendiente = 0.0
        fiado_vencido = 0.0
        fiado_clientes = set()
        fiado_tickets_abiertos = 0
        buckets = [0.0, 0.0, 0.0]  # 0-30 / 31-60 / +60
        for v in Venta.objects.filter(
            estado="completada", metodo_pago__nombre__iexact="Fiado"
        ).only("id", "total", "cliente_id", "creado_en"):
            pend = float(v.total or 0) - pagos_por_venta.get(v.id, 0.0)
            if pend <= 0.009:
                continue
            fiado_tickets_abiertos += 1
            fiado_pendiente += pend
            if v.cliente_id:
                fiado_clientes.add(v.cliente_id)
            dias = (hoy - v.creado_en.date()).days
            if dias <= 30:
                buckets[0] += pend
            elif dias <= 60:
                buckets[1] += pend
            else:
                buckets[2] += pend
        fiado_vencido = buckets[1] + buckets[2]
        rangos = ("0-30 días", "31-60 días", "Más de 60")
        fiado_aging = [
            {
                "rango": rangos[i],
                "total": buckets[i],
                "pct": round(buckets[i] / fiado_pendiente * 100, 1) if fiado_pendiente else 0,
            }
            for i in range(3)
        ]

        # =========================
        # ⚠ ALERTAS E INCIDENCIAS (prever errores antes de que cuesten dinero)
        # =========================
        alertas = []
        if n_agotados > 0:
            alertas.append({
                "nivel": "crit", "icono": "package-x",
                "titulo": f"{n_agotados} producto{'s' if n_agotados != 1 else ''} agotado{'s' if n_agotados != 1 else ''}",
                "texto": "Sin existencias: no se puede vender hasta reponer",
                "url": reverse("home_app:lista_productos"), "accion": "Ver productos",
            })
        if n_bajo_minimo > 0:
            alertas.append({
                "nivel": "warn", "icono": "alert-triangle",
                "titulo": f"{n_bajo_minimo} producto{'s' if n_bajo_minimo != 1 else ''} bajo mínimo",
                "texto": "Prevé la reposición antes de que se agoten",
                "url": reverse("home_app:lista_productos"), "accion": "Reponer",
            })
        if fiado_pendiente > 0:
            if fiado_vencido > 0:
                texto_fiado = f"{len(fiado_clientes)} cliente{'s' if len(fiado_clientes) != 1 else ''} · {fiado_vencido:.2f} € con más de 30 días"
                nivel_fiado = "crit"
            else:
                texto_fiado = f"{len(fiado_clientes)} cliente{'s' if len(fiado_clientes) != 1 else ''} con deuda abierta"
                nivel_fiado = "warn"
            alertas.append({
                "nivel": nivel_fiado, "icono": "wallet",
                "titulo": f"Fiado: {fiado_pendiente:.2f} € por cobrar",
                "texto": texto_fiado,
                "url": reverse("fiado_lista"), "accion": "Cobrar",
            })
        if excepciones_iva:
            n_exc = len(excepciones_iva)
            alertas.append({
                "nivel": "crit", "icono": "shield-alert",
                "titulo": f"{n_exc} ticket{'s' if n_exc != 1 else ''} con IVA fuera de norma",
                "texto": "Hay tickets con un IVA efectivo distinto al esperado",
                "url": "#seccion-auditoria", "accion": "Auditar",
            })
        if total_descuentos_periodo > 0:
            n_desc = ventas_con_descuento.count()
            alertas.append({
                "nivel": "info", "icono": "badge-percent",
                "titulo": f"{total_descuentos_periodo:.2f} € aplicados en descuentos",
                "texto": f"{n_desc} ticket{'s' if n_desc != 1 else ''} con descuento en este periodo",
                "url": "#seccion-auditoria", "accion": "Revisar",
            })
        if total_devoluciones_periodo > 0:
            alertas.append({
                "nivel": "info", "icono": "undo",
                "titulo": f"Devoluciones: {total_devoluciones_periodo:.2f} € devueltos",
                "texto": "Notas de crédito de este periodo (ya descontadas de los KPI y donuts)",
                "url": reverse("home_app:lista_ventas"), "accion": "Ver ventas",
            })

        # Cuentas por pagar a proveedores (compras recibidas sin saldar)
        total_por_pagar = 0.0
        n_por_pagar = 0
        por_pagar_vencido = 0.0
        for cp in CompraProveedor.objects.filter(estado="recibida").annotate(pagado=Sum("pagos__cantidad")):
            pend = float(cp.total or 0) - float(cp.pagado or 0)
            if pend > 0.009:
                total_por_pagar += pend
                n_por_pagar += 1
                if cp.fecha and (hoy - cp.fecha).days > 30:
                    por_pagar_vencido += pend
        if total_por_pagar > 0:
            texto_cp = f"{n_por_pagar} compra{'s' if n_por_pagar != 1 else ''} recibida{'s' if n_por_pagar != 1 else ''} sin saldar"
            if por_pagar_vencido > 0:
                texto_cp += f" · {por_pagar_vencido:.2f} € con más de 30 días"
            alertas.append({
                "nivel": "warn", "icono": "truck",
                "titulo": f"Por pagar a proveedores: {total_por_pagar:.2f} €",
                "texto": texto_cp,
                "url": reverse("purchases_app:compra_list"), "accion": "Ver compras",
            })

        context.update({
            "hoy": hoy,
            "iva_actual": iva_actual,
            "health_status": health_status,
            "health_color": health_color,
            "n_agotados": n_agotados,
            "n_bajo_minimo": n_bajo_minimo,
            "total_hoy": total_hoy,
            "total_mes_actual": total_mes_actual,
            "total_mes_anterior": total_mes_anterior,
            "total_anio_actual": total_anio_actual,
            "tickets_hoy": tickets_hoy,
            "tickets_mes": tickets_mes,
            "ticket_promedio_hoy": round(float(ticket_promedio_hoy), 2),
            "ticket_promedio_mes": round(float(ticket_promedio_mes), 2),
            "crecimiento": round(float(crecimiento), 2),
            "coste_total_mes": coste_total_mes,
            "beneficio_bruto": beneficio_bruto,
            "margen": round(float(margen), 2),
            "total_periodo": total_periodo,
            "tickets_periodo": tickets_periodo,
            "ticket_promedio_periodo": round(float(ticket_promedio_periodo), 2),
            "beneficio_periodo": beneficio_periodo,
            "margen_periodo": round(float(margen_periodo), 2),
            "productos_top": productos_top,
            "productos_ganancia": productos_ganancia,
            "productos_perdida": productos_perdida,
            "productos_criticos": productos_criticos,
            "categoria_stats": categoria_stats,
            "ventas_usuario": ventas_usuario,
            "recaudacion_filtrada": recaudacion_filtrada,
            "rango_activo": rango,
            "f_filtro_inicio": f_filtro_inicio,
            "f_filtro_fin": f_filtro_fin,
            "stock_muerto": stock_muerto,
            "stock_muerto_total": round(stock_muerto_total, 2),
            "stock_muerto_n": len(stock_muerto),
            "valor_venta_potencial": valor_venta_potencial,
            "ticker_eventos": ticker_eventos,
            "ultimas_ventas": ultimas_ventas,
            "productos_stock_bajo": productos_stock_bajo,
            "valor_total_inventario": valor_total_inventario,
            "total_productos_activos": total_productos_activos,
            "ventas_30_dias": ventas_por_dia,
            "dias_labels": dias_labels,
            "ventas_con_descuento": ventas_con_descuento[:10],
            "total_descuentos_periodo": total_descuentos_periodo,
            "total_devoluciones_periodo": total_devoluciones_periodo,
            "total_por_pagar": round(total_por_pagar, 2),
            "excepciones_iva": excepciones_iva[:10],
            "delta_periodo": delta_periodo,
            "delta_beneficio": delta_beneficio,
            "delta_ticket": delta_ticket,
            "delta_margen_pp": delta_margen_pp,
            "total_anterior": total_anterior,
            "mix_pagos": mix_pagos,
            "mix_categorias": mix_categorias,
            "fiado_pendiente": round(fiado_pendiente, 2),
            "fiado_vencido": round(fiado_vencido, 2),
            "fiado_clientes_n": len(fiado_clientes),
            "fiado_tickets_abiertos": fiado_tickets_abiertos,
            "fiado_aging": fiado_aging,
            "alertas": alertas,
        })
        return context
