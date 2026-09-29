# ============================================================
# CONTABILIDAD LIGERA — Cuenta de resultados (P&L)
#                + Libro de IVA del periodo
# ------------------------------------------------------------
# /reporting/contabilidad/  (mismos filtros de rango que el
# dashboard, reutilizando resolver_rango de exports.py)
# ============================================================
from django.db.models import Sum
from django.urls import reverse
from django.views.generic import TemplateView

from applications.cashflow.models import Movimiento
from applications.home.models import DetalleVenta, Devolucion, Venta
from applications.purchases.models import Compra as CompraProveedor

from .exports import resolver_rango


class ContabilidadView(TemplateView):
    template_name = "reporting/contabilidad.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        rango, inicio, fin = resolver_rango(self.request)
        tasa = 0.15  # IVA de ventas incluido en precios (KUDEA)

        # ------------------------------------------------
        # 1) INGRESOS (ventas netas del periodo)
        # ------------------------------------------------
        ventas = Venta.objects.filter(
            creado_en__date__range=(inicio, fin), estado="completada"
        )
        ventas_brutas = float(ventas.aggregate(t=Sum("total"))["t"] or 0)
        descuentos = float(ventas.aggregate(t=Sum("descuento"))["t"] or 0)
        devoluciones = float(
            Devolucion.objects.filter(creado_en__date__range=(inicio, fin))
            .aggregate(t=Sum("total"))["t"] or 0
        )
        ingresos_netos = round(ventas_brutas - devoluciones, 2)

        # ------------------------------------------------
        # 2) GASTOS (dinero que salió: pagos a proveedor + otros)
        # ------------------------------------------------
        gastos = Movimiento.objects.filter(
            fecha__date__range=(inicio, fin), tipo="gasto"
        )
        pagos_proveedor = float(
            gastos.filter(external_ref__startswith="compra:")
            .aggregate(t=Sum("cantidad"))["t"] or 0
        )
        otros_gastos = float(
            gastos.exclude(external_ref__startswith="compra:")
            .aggregate(t=Sum("cantidad"))["t"] or 0
        )
        total_gastos = round(pagos_proveedor + otros_gastos, 2)
        gastos_por_cuenta = list(
            gastos.values("cuenta__nombre")
            .annotate(total=Sum("cantidad"))
            .order_by("-total")
        )

        # ------------------------------------------------
        # 3) RESULTADO + margen de mercancía (CMV)
        # ------------------------------------------------
        resultado = round(ingresos_netos - total_gastos, 2)

        detalles = DetalleVenta.objects.filter(venta__in=ventas).select_related("producto")
        cmv = 0.0
        hay_costos = False
        for d in detalles:
            if d.producto.costo is not None:
                hay_costos = True
                cmv += float(d.cantidad) * float(d.producto.costo)
        dev_items = Devolucion.objects.filter(
            creado_en__date__range=(inicio, fin)
        ).values_list("items__detalle__producto__costo", "items__cantidad")
        cmv_devuelto = 0.0
        for costo, cant in dev_items:
            if costo is not None and cant:
                cmv_devuelto += float(costo) * float(cant)
        cmv_neto = round(max(0.0, cmv - cmv_devuelto), 2)
        margen_bruto = round(ingresos_netos - cmv_neto, 2)
        margen_pct = round(margen_bruto / ingresos_netos * 100, 1) if ingresos_netos else 0.0

        # ------------------------------------------------
        # 4) LIBRO DE IVA (repercutido − soportado)
        # ------------------------------------------------
        # Repercutido: precios con 15% incluido → base = total / 1.15
        base_repercutida = round(ventas_brutas / (1 + tasa), 2)
        cuota_repercutida = round(ventas_brutas - base_repercutida, 2)
        base_devoluciones = round(devoluciones / (1 + tasa), 2)
        cuota_devoluciones = round(devoluciones - base_devoluciones, 2)
        base_reper_neta = round(base_repercutida - base_devoluciones, 2)
        cuota_reper_neta = round(cuota_repercutida - cuota_devoluciones, 2)

        # Soportado: compras recibidas con fecha de factura en el periodo
        compras = CompraProveedor.objects.filter(
            estado="recibida", fecha__range=(inicio, fin)
        )
        base_soportada = float(compras.aggregate(t=Sum("subtotal"))["t"] or 0)
        cuota_soportada = float(compras.aggregate(t=Sum("iva"))["t"] or 0)
        n_compras = compras.count()

        cuota_liquidar = round(cuota_reper_neta - cuota_soportada, 2)

        ctx.update({
            "rango_activo": rango,
            "f_filtro_inicio": inicio,
            "f_filtro_fin": fin,
            "tasa_iva": int(tasa * 100),
            # Ingresos
            "ventas_brutas": round(ventas_brutas, 2),
            "descuentos_periodo": round(descuentos, 2),
            "devoluciones_periodo": round(devoluciones, 2),
            "ingresos_netos": ingresos_netos,
            "tickets_periodo": ventas.count(),
            # Gastos
            "pagos_proveedor": round(pagos_proveedor, 2),
            "otros_gastos": round(otros_gastos, 2),
            "total_gastos": total_gastos,
            "gastos_por_cuenta": [
                {"nombre": g["cuenta__nombre"] or "—", "total": float(g["total"])}
                for g in gastos_por_cuenta
            ],
            # Resultado + margen
            "resultado": resultado,
            "cmv": cmv_neto,
            "hay_costos": hay_costos,
            "margen_bruto": margen_bruto,
            "margen_pct": margen_pct,
            # Libro de IVA
            "base_repercutida": base_repercutida,
            "cuota_repercutida": cuota_repercutida,
            "base_devoluciones": base_devoluciones,
            "cuota_devoluciones": cuota_devoluciones,
            "base_reper_neta": base_reper_neta,
            "cuota_reper_neta": cuota_reper_neta,
            "base_soportada": round(base_soportada, 2),
            "cuota_soportada": round(cuota_soportada, 2),
            "n_compras": n_compras,
            "cuota_liquidar": cuota_liquidar,
            "url_dashboard": reverse("reporting_app:dashboard_informes"),
        })
        return ctx
