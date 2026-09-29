# =====================================================================
# 📁 VISTAS · APP 'purchases' — Proveedores, compras, recepción (stock+costo) y pagos
# =====================================================================
#   L40    class CompraListView(LoginRequiredMixin, ListView):
#   L84    class ProveedorListView(LoginRequiredMixin, ListView):
#   L110   class ProveedorCreateView(LoginRequiredMixin, CreateView):
#   L128   class ProveedorUpdateView(LoginRequiredMixin, UpdateView):
#   L152   class CompraCreateView(LoginRequiredMixin, View):
#   L200   class CompraDetailView(LoginRequiredMixin, DetailView):
#   L214   def compra_recibir(request, pk):
#   L252   def compra_cancelar(request, pk):
#   L274   def pedido_pdf(request):
#   L322   def informe_compras(request):
#   L438   def compra_pagar(request, pk):
# =====================================================================

# ============================================================
# VISTAS DEL MÓDULO DE COMPRAS (app: purchases)
# ------------------------------------------------------------
# SECCIONES:
#   1) COMPRAS     — lista de compras con filtros y totales
#   2) PROVEEDORES — lista, alta y edición de proveedores
#   3) NUEVA COMPRA — cabecera + líneas (formset)
#   4) DETALLE     — ver, recibir (sube stock) y cancelar
#   5) PDF PEDIDO  — reposición agrupada por proveedor
#   6) INFORMES    — gasto por proveedor + margen por producto
# ============================================================
from datetime import date, timedelta
from decimal import Decimal, ROUND_HALF_UP

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import transaction
from django.db.models import Count, DecimalField, ExpressionWrapper, F, Q, Sum
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.template.loader import render_to_string
from django.urls import reverse_lazy
from django.utils import timezone
from django.views.decorators.http import require_POST
from django.views.generic import CreateView, DetailView, ListView, UpdateView, View

from applications.product.models import Producto
from applications.stock.models import Movement

from .forms import CompraForm, CompraItemFormSet, ProveedorForm
from .models import Compra, CompraItem, Proveedor, PagoCompra


# ============================================================
# 1) LISTA DE COMPRAS  →  /compras/
#    Muestra las compras con su estado (borrador/recibida/
#    cancelada) y los totales del periodo.
# ============================================================
class CompraListView(LoginRequiredMixin, ListView):
    model = Compra
    template_name = 'purchases/compra_list.html'
    context_object_name = 'compras'
    paginate_by = 25

    def get_queryset(self):
        queryset = super().get_queryset().select_related('proveedor')

        # Filtro de texto: nº de compra o nombre del proveedor
        search = (self.request.GET.get('search') or '').strip()
        if search:
            queryset = queryset.filter(
                Q(numero__icontains=search) | Q(proveedor__nombre__icontains=search)
            )

        # Filtro por estado
        estado = self.request.GET.get('estado')
        if estado in dict(Compra.ESTADOS):
            queryset = queryset.filter(estado=estado)

        return queryset

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)

        # Datos de las tarjetas de cabecera (siempre sobre TODAS las compras)
        todas = Compra.objects.all()
        ctx['title'] = 'Compras'
        ctx['total_compras'] = todas.count()
        ctx['compras_borrador'] = todas.filter(estado='borrador').count()
        ctx['gasto_total'] = todas.filter(estado='recibida').aggregate(t=Sum('total'))['t'] or 0
        ctx['proveedores_activos'] = Proveedor.objects.filter(activo=True).count()
        ctx['estado_actual'] = self.request.GET.get('estado', '')
        ctx['search_actual'] = self.request.GET.get('search', '')
        return ctx


# ============================================================
# 2) PROVEEDORES
#    2a) Lista      → /compras/proveedores/
#    2b) Alta       → /compras/proveedores/nuevo/
#    2c) Edición    → /compras/proveedores/<id>/editar/
# ============================================================
class ProveedorListView(LoginRequiredMixin, ListView):
    model = Proveedor
    template_name = 'purchases/proveedor_list.html'
    context_object_name = 'proveedores'
    paginate_by = 25

    def get_queryset(self):
        queryset = super().get_queryset()
        search = (self.request.GET.get('search') or '').strip()
        if search:
            queryset = queryset.filter(
                Q(nombre__icontains=search) |
                Q(nit__icontains=search) |
                Q(contacto__icontains=search)
            )
        return queryset

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['title'] = 'Proveedores'
        ctx['search_actual'] = self.request.GET.get('search', '')
        ctx['total_proveedores'] = Proveedor.objects.count()
        ctx['proveedores_activos'] = Proveedor.objects.filter(activo=True).count()
        return ctx


class ProveedorCreateView(LoginRequiredMixin, CreateView):
    model = Proveedor
    form_class = ProveedorForm
    template_name = 'purchases/proveedor_form.html'
    success_url = reverse_lazy('purchases_app:proveedor_list')

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['title'] = 'Nuevo proveedor'
        ctx['es_edicion'] = False
        return ctx

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, 'Proveedor creado correctamente')
        return response


class ProveedorUpdateView(LoginRequiredMixin, UpdateView):
    model = Proveedor
    form_class = ProveedorForm
    template_name = 'purchases/proveedor_form.html'
    success_url = reverse_lazy('purchases_app:proveedor_list')

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['title'] = 'Editar proveedor'
        ctx['es_edicion'] = True
        return ctx

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, 'Proveedor actualizado correctamente')
        return response


# ============================================================
# 3) CREAR COMPRA  →  /compras/nueva/
#    Cabecera (proveedor/fecha) + tabla de líneas en la misma
#    pantalla. Al guardar queda en estado "borrador"; el stock
#    sólo se toca al pulsar "Recibir mercancía" (sección 4).
# ============================================================
class CompraCreateView(LoginRequiredMixin, View):
    template_name = 'purchases/compra_form.html'

    def get(self, request):
        return self._render(request, CompraForm(), CompraItemFormSet(instance=Compra()))

    def post(self, request):
        form = CompraForm(request.POST)
        # Las líneas se validan ANTES de guardar la cabecera para no
        # dejar compras vacías si algo falla.
        formset = CompraItemFormSet(request.POST, instance=Compra())

        if form.is_valid() and formset.is_valid():
            compra = form.save(commit=False)
            compra.creada_por = request.user
            compra.save()

            # Reapuntar las líneas a la compra ya guardada y guardarlas
            formset.instance = compra
            for linea_form in formset.forms:
                linea_form.instance.compra = compra
            formset.save()

            if not compra.items.exists():
                # Ninguna fila tenía producto: no se crea la compra
                compra.delete()
                form.add_error(None, 'Añade al menos un producto a la compra.')
            else:
                messages.success(request, f'Compra {compra.numero} creada en borrador.')
                return redirect('purchases_app:compra_detail', pk=compra.pk)

        return self._render(request, form, formset)

    def _render(self, request, form, formset):
        return render(request, self.template_name, {
            'title': 'Nueva compra',
            'form': form,
            'formset': formset,
            'es_nueva': True,
        })


# ============================================================
# 4) DETALLE, RECEPCIÓN Y CANCELACIÓN
#    4a) Detalle   → /compras/<id>/
#    4b) Recibir   → /compras/<id>/recibir/  (sube stock + movimiento)
#    4c) Cancelar  → /compras/<id>/cancelar/ (no toca stock)
# ============================================================
class CompraDetailView(LoginRequiredMixin, DetailView):
    model = Compra
    template_name = 'purchases/compra_detail.html'
    context_object_name = 'compra'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['title'] = f'Compra {self.object.numero}'
        ctx['items'] = self.object.items.select_related('producto')
        return ctx


@require_POST
@login_required
def compra_recibir(request, pk):
    """Recibe la mercancía: sube el stock de cada producto (como una
    Entrada en Movimientos), actualiza su coste de compra y marca la
    compra como recibida. Una compra sólo puede recibirse una vez."""
    compra = get_object_or_404(Compra, pk=pk)

    if compra.estado != 'borrador':
        messages.warning(request, f'La compra {compra.numero} ya está {compra.get_estado_display().lower()}.')
        return redirect('purchases_app:compra_detail', pk=compra.pk)

    if not compra.items.exists():
        messages.error(request, 'La compra no tiene líneas: añade productos antes de recibirla.')
        return redirect('purchases_app:compra_detail', pk=compra.pk)

    with transaction.atomic():
        for item in compra.items.select_related('producto'):
            # 1) Stock: entrada registrada en Movimientos con el origen "Compra COM-XXXXXX"
            Movement.objects.create(
                producto=item.producto,
                cantidad=item.cantidad,
                tipo='entrada',
                observaciones=f'Compra {compra.numero} · {compra.proveedor.nombre}',
            )
            # 2) Coste real del producto (para saber el margen)
            item.producto.costo = item.precio_unitario
            item.producto.save(update_fields=['costo'])

        # 3) Estado de la compra
        compra.estado = 'recibida'
        compra.recibida_en = timezone.now()
        compra.save(update_fields=['estado', 'recibida_en'])

    messages.success(request, f'Compra {compra.numero} recibida: stock actualizado.')
    return redirect('purchases_app:compra_detail', pk=compra.pk)


@require_POST
@login_required
def compra_cancelar(request, pk):
    """Cancela la compra sin tocar el stock (sólo si está en borrador)."""
    compra = get_object_or_404(Compra, pk=pk)

    if compra.estado != 'borrador':
        messages.warning(request, f'La compra {compra.numero} ya está {compra.get_estado_display().lower()}.')
    else:
        compra.estado = 'cancelada'
        compra.save(update_fields=['estado'])
        messages.success(request, f'Compra {compra.numero} cancelada.')
    return redirect('purchases_app:compra_detail', pk=compra.pk)


# ============================================================
# 5) PDF DE PEDIDO DE REPOSICIÓN  →  /compras/pedido-pdf/
#    Coge los productos por debajo de su stock mínimo y los
#    agrupa por PROVEEDOR HABITUAL para pedir con un clic.
# ============================================================
from weasyprint import HTML  # noqa: E402  (import tardío: sólo lo usa este PDF)


@login_required
def pedido_pdf(request):
    """PDF con los productos bajo mínimo, agrupados por proveedor."""
    # 1) Productos activos por debajo de su mínimo (los del "stock bajo")
    bajos = (
        Producto.objects.filter(activo=True)
        .filter(stock__lt=F('stock_minimo'))
        .select_related('proveedor', 'categoria')
        .order_by('proveedor__nombre', 'nombre')
    )

    # 2) Agrupar por proveedor: {proveedor_o_None: [líneas]}
    grupos = {}
    for p in bajos:
        clave = p.proveedor  # None = "Sin proveedor asignado"
        grupos.setdefault(clave, []).append({
            'producto': p,
            'faltan': max(p.stock_minimo - p.stock, 0),
        })

    # 3) Los con proveedor primero; "sin proveedor" al final
    ordenados = sorted(
        grupos.items(),
        key=lambda kv: (kv[0] is None, (kv[0].nombre.lower() if kv[0] else '')),
    )

    html_string = render_to_string('purchases/pedido_pdf.html', {
        'grupos': ordenados,
        'total_lineas': sum(len(v) for v in grupos.values()),
        'total_proveedores': sum(1 for k in grupos if k is not None),
        'fecha': timezone.now(),
    })

    pdf = HTML(string=html_string).write_pdf()
    response = HttpResponse(pdf, content_type='application/pdf')
    response['Content-Disposition'] = (
        f'attachment; filename="pedido_reposicion_{timezone.now().strftime("%Y%m%d_%H%M")}.pdf"'
    )
    return response


# ============================================================
# 6) INFORME DE COMPRAS  →  /compras/informes/
#    6a) GASTO POR PROVEEDOR en un periodo (libro de compras)
#    6b) MARGEN POR PRODUCTO: coste de compra vs precio de venta
#        (el precio de venta va con IVA, el de compra sin IVA,
#         por eso al comparar quitamos el IVA al PVP)
# ============================================================
@login_required
def informe_compras(request):
    hoy = timezone.localdate()

    # ---- Filtros GET: desde / hasta / proveedor ----
    desde_str = request.GET.get('desde') or ''
    hasta_str = request.GET.get('hasta') or ''
    proveedor_id = (request.GET.get('proveedor') or '').strip()

    try:
        desde = date.fromisoformat(desde_str) if desde_str else hoy - timedelta(days=30)
    except ValueError:
        desde = hoy - timedelta(days=30)
    try:
        hasta = date.fromisoformat(hasta_str) if hasta_str else hoy
    except ValueError:
        hasta = hoy

    # Compras que cuentan (las canceladas no generan gasto)
    compras = Compra.objects.filter(
        estado__in=('borrador', 'recibida'),
        fecha__gte=desde, fecha__lte=hasta,
    )
    if proveedor_id.isdigit():
        compras = compras.filter(proveedor_id=proveedor_id)

    # ---- 6a) Totales por proveedor ----
    por_proveedor = list(
        compras.values('proveedor_id', 'proveedor__nombre')
        .annotate(
            n_compras=Count('id'),
            n_recibidas=Count('id', filter=Q(estado='recibida')),
            base=Sum('subtotal'),
            iva=Sum('iva'),
            total=Sum('total'),
        )
        .order_by('-total')
    )
    totales = compras.aggregate(
        n=Count('id'), base=Sum('subtotal'), iva=Sum('iva'), total=Sum('total')
    )

    # ---- 6b) Líneas por producto: unidades y coste ----
    lineas = (
        CompraItem.objects.filter(compra__in=compras)
        .values(
            'producto_id', 'producto__nombre',
            'producto__precio', 'producto__porcentaje_iva',
        )
        .annotate(
            unidades=Sum('cantidad'),
            n_compras=Count('compra', distinct=True),
            coste=Sum(ExpressionWrapper(
                F('cantidad') * F('precio_unitario'),
                output_field=DecimalField(max_digits=14, decimal_places=2),
            )),
        )
        .order_by('-coste')
    )

    productos = []
    for l in lineas:
        unidades = l['unidades'] or 0
        coste = l['coste'] or Decimal('0')
        costo_medio = (coste / unidades) if unidades else Decimal('0')

        # PVP del producto (IVA incluido) -> lo pasamos a BASE para comparar
        pvp = l['producto__precio'] or Decimal('0')
        iva_p = l['producto__porcentaje_iva'] or Decimal('0')
        precio_base = (pvp / (Decimal('1') + iva_p / Decimal('100'))).quantize(
            Decimal('0.01'), rounding=ROUND_HALF_UP
        )

        margen_unit = precio_base - costo_medio
        margen_pct = (margen_unit / precio_base * 100) if precio_base > 0 else Decimal('0')

        productos.append({
            'id': l['producto_id'],
            'nombre': l['producto__nombre'],
            'unidades': unidades,
            'n_compras': l['n_compras'],
            'coste': coste,
            'costo_medio': costo_medio,
            'precio_base': precio_base,
            'margen_unit': margen_unit,
            'margen_pct': margen_pct,
        })

    # KPIs del margen (ponderado por lo comprado)
    unidades_totales = sum(p['unidades'] for p in productos)
    margen_total_pct = Decimal('0')
    if productos:
        ingreso_potencial = sum(p['precio_base'] * p['unidades'] for p in productos)
        coste_total = sum(p['coste'] for p in productos)
        if ingreso_potencial > 0:
            margen_total_pct = ((ingreso_potencial - coste_total) / ingreso_potencial * 100)

    return render(request, 'purchases/informe_compras.html', {
        'title': 'Informe de compras',
        'desde': desde.isoformat(),
        'hasta': hasta.isoformat(),
        'proveedor_id': proveedor_id,
        'proveedores': Proveedor.objects.all(),
        'por_proveedor': por_proveedor,
        'totales': totales,
        'productos': productos,
        'unidades_totales': unidades_totales,
        'margen_total_pct': margen_total_pct,
    })


# ============================================================
# 7) PAGO A PROVEEDOR (cuentas por pagar)
#    POST /compras/<pk>/pagar/
# ============================================================
@require_POST
@login_required
def compra_pagar(request, pk):
    """Registra un pago total o parcial de una compra recibida.

    Crea el PagoCompra, descuenta la deuda y mueve el dinero
    de Caja (efectivo) o Banco (tarjeta) como gasto.
    """
    compra = get_object_or_404(Compra, pk=pk)

    if compra.estado != "recibida":
        messages.warning(request, f"Sólo se registran pagos de compras recibidas (la {compra.numero} está en '{compra.get_estado_display().lower()}').")
        return redirect("purchases_app:compra_detail", pk=compra.pk)

    try:
        cantidad = Decimal(str(request.POST.get("cantidad", "")).replace(",", "."))
    except Exception:
        cantidad = Decimal("0")
    metodo = request.POST.get("metodo", "efectivo")
    if metodo not in ("efectivo", "tarjeta"):
        metodo = "efectivo"
    notas = (request.POST.get("notas") or "").strip()

    pendiente = compra.pendiente_pago
    if cantidad <= 0:
        messages.error(request, "El importe del pago debe ser mayor que 0.")
        return redirect("purchases_app:compra_detail", pk=compra.pk)
    if cantidad > pendiente:
        messages.error(request, f"Sólo falta pagar {pendiente:.2f} € de la {compra.numero}.")
        return redirect("purchases_app:compra_detail", pk=compra.pk)

    from applications.cashflow.models import Cuenta, Movimiento
    from applications.cashflow.services import register_movement

    with transaction.atomic():
        pago = PagoCompra.objects.create(
            compra=compra, cantidad=cantidad, metodo=metodo,
            usuario=request.user, notas=notas,
        )
        cuenta_nombre = "Caja" if metodo == "efectivo" else "Banco"
        cuenta, _ = Cuenta.objects.get_or_create(nombre=cuenta_nombre)
        register_movement(
            concepto=f"Pago a {compra.proveedor.nombre} · {compra.numero}",
            tipo=Movimiento.Tipo.GASTO,
            origen=Movimiento.Origen.FACTURA,
            cuenta=cuenta,
            cantidad=cantidad,
            external_ref=f"compra:{compra.pk}:pago:{pago.pk}",
            created_by=request.user,
        )

    restante = compra.pendiente_pago
    if restante <= 0:
        messages.success(request, f"{compra.numero} pagada al completo ({cantidad:.2f} €). Deuda saldada.")
    else:
        messages.success(request, f"Pago de {cantidad:.2f} € registrado. Quedan {restante:.2f} € por pagar a {compra.proveedor.nombre}.")
    return redirect("purchases_app:compra_detail", pk=compra.pk)
