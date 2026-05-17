from django.views.generic import TemplateView
from django.utils.timezone import localdate
from django.db import models
from django.db.models import Sum, F, Count, ExpressionWrapper
from django.db.models.functions import ExtractHour
from datetime import timedelta

from applications.home.models import Venta, DetalleVenta
from applications.product.models import Producto
from applications.config.models import ConfiguracionFiscal


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

        # =========================
        # Ventas HOY / MES / AÑO
        # =========================
        ventas_hoy = Venta.objects.filter(creado_en__date=hoy, estado="completada")
        ventas_mes = Venta.objects.filter(creado_en__date__range=(inicio_mes, hoy), estado="completada")
        ventas_anio = Venta.objects.filter(creado_en__date__range=(inicio_anio, hoy), estado="completada")

        total_hoy = float(ventas_hoy.aggregate(total=Sum("total"))["total"] or 0)
        total_mes_actual = float(ventas_mes.aggregate(total=Sum("total"))["total"] or 0)
        total_anio_actual = float(ventas_anio.aggregate(total=Sum("total"))["total"] or 0)

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
        ticket_promedio_periodo = (total_periodo / tickets_periodo) if tickets_periodo else 0

        # Margen del periodo filtrado (Operaciones puras en float)
        detalles_periodo = DetalleVenta.objects.filter(venta__in=ventas_periodo).annotate(
            coste_item=ExpressionWrapper(F("cantidad") * F("producto__costo"), output_field=models.FloatField())
        )
        coste_total_periodo = float(detalles_periodo.aggregate(total=Sum("coste_item"))["total"] or 0)
        
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
            "excepciones_iva": excepciones_iva[:10],
        })
        return context