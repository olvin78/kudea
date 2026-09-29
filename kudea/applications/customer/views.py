# =====================================================================
# 📁 VISTAS · APP 'customer' — CRM de clientes + fiado (cuenta corriente y cobros)
# =====================================================================
#   L11    class CustomerCreateView(CreateView):
#   L34    def search_cliente(request):
#   L76    def _tickets_fiado():
#   L88    def _tickets_fiado_pagados():
#   L101   def fiado_lista(request):
#   L169   def fiado_cobrar(request, venta_id):
#   L251   def fiado_recibo(request, pago_id):
#   L273   def fiado_cliente_nuevo(request):
#   L293   def fiado_cliente_editar(request, cliente_id):
#   L313   def fiado_cliente_eliminar(request, cliente_id):
#   L332   def cliente_ajax(request):
#   L358   class ListaClientesView(LoginRequiredMixin, ListView):
#   L393   class FichaClienteView(LoginRequiredMixin, DetailView):
# =====================================================================

from django.shortcuts import render, redirect
from django.views.generic.edit import CreateView
from .models import Cliente, PagoFiado
from .forms import ClienteForm
from django.urls import reverse_lazy
from django.http import JsonResponse




class CustomerCreateView(CreateView):
    model = Cliente
    form_class = ClienteForm
    template_name = 'customer/nuevo_cliente.html'
    success_url = reverse_lazy('tpv_shop:home')  # Redirige al home después de guardar

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form_title'] = 'Crear un nuevo cliente'
        return context

    # Buscar cliente por DNI (para autocompletar)
    def get(self, request, *args, **kwargs):
        dni = request.GET.get('dni')
        if dni:
            try:
                cliente = Cliente.objects.get(dni=dni)
                return JsonResponse({'nombre': cliente.nombre, 'codigo_postal': cliente.codigo_postal, 'correo': cliente.correo, 'telefono': cliente.telefono})
            except Cliente.DoesNotExist:
                return JsonResponse({'error': 'Cliente no encontrado'}, status=404)
        return super().get(request, *args, **kwargs)


def search_cliente(request):
    dni = request.GET.get('dni', None)
    if dni:
        try:
            cliente = Cliente.objects.get(dni=dni)
            data = {
                'found': True,
                'cliente': {
                    'nombre': cliente.nombre,
                    'dni': cliente.dni,
                    'codigo_postal': cliente.codigo_postal,
                    'correo': cliente.correo,
                    'telefono': cliente.telefono
                }
            }
        except Cliente.DoesNotExist:
            data = {'found': False}
    else:
        data = {'found': False}
    
    return JsonResponse(data)


# ============================================================
#  FIADO (cuenta corriente de cliente)
#   - /fiado/                     pantalla con deudores
#   - /fiado/cobrar/<venta_id>/    el cliente paga (total o parcial)
#   - /fiado/recibo/<pago_id>/     recibo imprimible del pago
#   - /clientes/nuevo-ajax/        alta rápida desde el TPV
# ============================================================
from decimal import Decimal
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.db.models import Sum
from django.shortcuts import get_object_or_404
from django.views.decorators.http import require_POST

from applications.home.models import Venta
from applications.payments.models import MetodoPago


def _tickets_fiado():
    """Tickets de fiado que siguen con dinero por cobrar."""
    ventas = (
        Venta.objects.filter(metodo_pago__nombre__iexact="Fiado")
        .exclude(estado="cancelada")
        .select_related("cliente", "metodo_pago")
        .prefetch_related("pagos_fiado")
        .order_by("-creado_en")
    )
    return [v for v in ventas if v.pendiente_fiado > 0]


def _tickets_fiado_pagados():
    """Tickets de fiado YA liquidados (histórico, sólo lectura)."""
    ventas = (
        Venta.objects.filter(metodo_pago__nombre__iexact="Fiado")
        .exclude(estado="cancelada")
        .select_related("cliente", "metodo_pago")
        .prefetch_related("pagos_fiado")
        .order_by("-creado_en")
    )
    return [v for v in ventas if v.pendiente_fiado <= 0 and v.pagado_fiado > 0]


@login_required
def fiado_lista(request):
    """Pantalla principal: cuánto se debe, por quién y cobrar."""
    ventas = _tickets_fiado()

    # Búsqueda: cliente (nombre/dni/teléfono) o código de ticket
    q = request.GET.get("q", "").strip()
    if q:
        ql = q.casefold()
        filtradas = []
        for v in ventas:
            c = v.cliente
            texto = " ".join([
                str(v.codigo or ""),
                str(c.nombre) if c else "",
                str(c.dni) if c and c.dni else "",
                str(c.telefono) if c and c.telefono else "",
            ]).casefold()
            if ql in texto:
                filtradas.append(v)
        ventas = filtradas

    # Resumen agrupado por cliente (de mayor a menor deuda)
    deudores = {}
    for v in ventas:
        if not v.cliente:
            continue
        d = deudores.setdefault(v.cliente.id, {
            "cliente": v.cliente, "tickets": 0, "deuda": Decimal("0"),
        })
        d["tickets"] += 1
        d["deuda"] += v.pendiente_fiado
    deudores = sorted(deudores.values(), key=lambda x: x["deuda"], reverse=True)

    # Agenda completa (para el popup "Todos los clientes") con deuda por cliente
    debe_map = dict(
        Venta.objects.filter(metodo_pago__nombre__iexact="Fiado")
        .exclude(estado="cancelada")
        .values("cliente_id")
        .annotate(t=Sum("total"))
        .values_list("cliente_id", "t")
    )
    pagado_map = dict(
        PagoFiado.objects.exclude(venta__cliente__isnull=True)
        .values("venta__cliente_id")
        .annotate(t=Sum("cantidad"))
        .values_list("venta__cliente_id", "t")
    )
    clientes = [
        {"obj": c,
         "deuda": (debe_map.get(c.id) or 0) - (pagado_map.get(c.id) or 0)}
        for c in Cliente.objects.all()
    ]

    return render(request, "customer/fiado.html", {
        "ventas": ventas,
        "q": q,
        "deudores": deudores,
        "clientes": clientes,
        "pagados": _tickets_fiado_pagados(),
        "total_por_cobrar": sum(v.pendiente_fiado for v in ventas),
        "metodos_pago": MetodoPago.objects.filter(activo=True).exclude(
            nombre__iexact="Fiado"
        ),
    })


@require_POST
@login_required
def fiado_cobrar(request, venta_id):
    """Cobro total o parcial de un ticket → el dinero SÍ entra en caja.
    Acepta un método único o Pago Mixto (dos métodos: p. ej. la mitad
    en tarjeta y el resto en efectivo)."""
    from applications.cashflow.models import Cuenta, Movimiento
    from applications.cashflow.services import register_movement

    venta = get_object_or_404(Venta, pk=venta_id)
    pendiente = venta.pendiente_fiado

    def _num(valor):
        try:
            return Decimal(str(valor or "0"))
        except Exception:
            return Decimal("0")

    def _registrar(cantidad, metodo):
        es_efectivo = (not metodo) or metodo.nombre.lower() in ("efectivo", "cash", "fiado")
        cuenta, _ = Cuenta.objects.get_or_create(nombre="Caja" if es_efectivo else "Banco")
        with transaction.atomic():
            pago = PagoFiado.objects.create(
                venta=venta,
                cantidad=cantidad,
                metodo_pago=metodo,
                usuario=request.user,
            )
            register_movement(
                concepto=(
                    f"Cobro de fiado {venta.codigo} "
                    f"({venta.cliente.nombre if venta.cliente else 'sin cliente'})"
                ),
                tipo=Movimiento.Tipo.INGRESO,
                origen=Movimiento.Origen.TPV,
                cuenta=cuenta,
                cantidad=cantidad,
                metodo_pago=(
                    Movimiento.MetodoPago.EFECTIVO if es_efectivo
                    else Movimiento.MetodoPago.TARJETA
                ),
                external_ref=f"fiado:pago:{pago.id}",
                created_by=request.user,
            )
        return pago

    metodo = MetodoPago.objects.filter(id=request.POST.get("metodo_pago")).first()
    es_mixto = bool(metodo) and metodo.nombre.lower() == "pago mixto"

    if es_mixto:
        m1 = MetodoPago.objects.filter(id=request.POST.get("parte1_metodo")).first()
        m2 = MetodoPago.objects.filter(id=request.POST.get("parte2_metodo")).first()
        c1 = _num(request.POST.get("parte1_cantidad"))
        c2 = _num(request.POST.get("parte2_cantidad"))

        def _metodo_ok(m):
            return m is not None and m.nombre.lower() not in ("pago mixto", "fiado")

        if not (_metodo_ok(m1) and _metodo_ok(m2)):
            messages.error(request, "Pago mixto: elige dos métodos de pago válidos.")
            return redirect("fiado_lista")
        if c1 <= 0 or c2 <= 0:
            messages.error(request, "Pago mixto: las dos partes deben ser mayores que 0.")
            return redirect("fiado_lista")
        if c1 + c2 > pendiente:
            messages.error(request, f"Sólo falta cobrar {pendiente} € de ese ticket.")
            return redirect("fiado_lista")

        _registrar(c1, m1)
        ultimo = _registrar(c2, m2)
    else:
        cantidad = _num(request.POST.get("cantidad"))
        if cantidad <= 0:
            messages.error(request, "El importe debe ser mayor que 0.")
            return redirect("fiado_lista")
        if cantidad > pendiente:
            messages.error(request, f"Sólo falta cobrar {pendiente} € de ese ticket.")
            return redirect("fiado_lista")
        ultimo = _registrar(cantidad, metodo)

    return redirect("fiado_recibo", pago_id=ultimo.id)


@login_required
def fiado_recibo(request, pago_id):
    """Recibo imprimible del pago (ticket limpio como los demás)."""
    pago = get_object_or_404(
        PagoFiado.objects.select_related("venta__cliente", "metodo_pago", "usuario"),
        pk=pago_id,
    )
    return render(request, "customer/fiado_recibo.html", {
        "pago": pago,
        "venta": pago.venta,
        "saldo_restante": pago.venta.pendiente_fiado,
        "pagos": pago.venta.pagos_fiado.select_related("metodo_pago").order_by("creado_en"),
    })


# ------------------------------------------------------------
#  ALTA DE CLIENTE DESDE EL FIADO (formulario propio e
#  independiente del que usa tpv_shop)
# ------------------------------------------------------------
from .forms import ClienteFiadoForm


@login_required
def fiado_cliente_nuevo(request):
    """Formulario independiente para dar de alta un cliente y volver al fiado."""
    if request.method == "POST":
        form = ClienteFiadoForm(request.POST)
        if form.is_valid():
            cliente = form.save()
            messages.success(
                request,
                f"Cliente «{cliente.nombre}» creado. Ya puedes venderle a fiado.",
            )
            return redirect("fiado_lista")
        messages.error(request, "Revisa los datos del formulario.")
    else:
        form = ClienteFiadoForm()

    return render(request, "customer/fiado_nuevo_cliente.html", {"form": form})


@require_POST
@login_required
def fiado_cliente_editar(request, cliente_id):
    """Editar datos de un cliente desde el popup del fiado."""
    cliente = get_object_or_404(Cliente, pk=cliente_id)
    form = ClienteFiadoForm(request.POST, instance=cliente)
    if form.is_valid():
        form.save()
        messages.success(request, f"Datos de «{cliente.nombre}» actualizados.")
    else:
        errores = " ".join(
            " ".join(v) for v in form.errors.values()
        ).strip()
        messages.error(
            request,
            f"No se pudo guardar: {errores}" if errores else "Revisa los datos del formulario.",
        )
    return redirect("fiado_lista")


@require_POST
@login_required
def fiado_cliente_eliminar(request, cliente_id):
    """Eliminar un cliente (sólo si no tiene tickets asociados)."""
    cliente = get_object_or_404(Cliente, pk=cliente_id)
    n = cliente.ventas.count()
    if n:
        messages.error(
            request,
            f"No se puede eliminar «{cliente.nombre}»: tiene {n} ticket"
            f"{'s' if n != 1 else ''} asociado{'s' if n != 1 else ''}. "
            "Cancela o cobra esos tickets primero.",
        )
    else:
        nombre = cliente.nombre
        cliente.delete()
        messages.success(request, f"Cliente «{nombre}» eliminado.")
    return redirect("fiado_lista")


@require_POST
def cliente_ajax(request):
    """Alta de cliente en 2 segundos desde el popup de fiado del TPV."""
    if not request.user.is_authenticated:
        return JsonResponse({"ok": False, "error": "No autenticado"}, status=401)

    nombre = (request.POST.get("nombre") or "").strip()
    telefono = (request.POST.get("telefono") or "").strip()
    if not nombre:
        return JsonResponse({"ok": False, "error": "El nombre es obligatorio"}, status=400)

    cliente = Cliente.objects.create(nombre=nombre, telefono=telefono)
    return JsonResponse({"ok": True, "id": cliente.id, "nombre": cliente.nombre})


# ============================================================
#  CRM LIGERO — lista y ficha de cliente con historial
#    · GET /clientes/          → lista + buscador
#    · GET /clientes/<pk>/     → ficha, gasto, fiado e historial
# ============================================================
from django.db.models import Count, Sum, Max, Q
from django.views.generic import ListView, DetailView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404
from django.core.paginator import Paginator


class ListaClientesView(LoginRequiredMixin, ListView):
    model = Cliente
    template_name = "customer/cliente_lista.html"
    context_object_name = "clientes"
    paginate_by = 25

    def get_queryset(self):
        q = self.request.GET.get("q", "").strip()
        qs = (
            Cliente.objects.annotate(
                n_ventas=Count("ventas", filter=~Q(ventas__estado="cancelada")),
                total_gastado=Sum(
                    "ventas__total", filter=~Q(ventas__estado="cancelada")
                ),
                ultima_visita=Max(
                    "ventas__creado_en", filter=~Q(ventas__estado="cancelada")
                ),
            )
            .order_by("-ultima_visita", "nombre")
        )
        if q:
            qs = qs.filter(
                Q(nombre__icontains=q)
                | Q(dni__icontains=q)
                | Q(correo__icontains=q)
                | Q(telefono__icontains=q)
            )
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["q"] = self.request.GET.get("q", "").strip()
        return context


class FichaClienteView(LoginRequiredMixin, DetailView):
    model = Cliente
    template_name = "customer/cliente_ficha.html"
    context_object_name = "cliente"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        cliente = self.object
        ventas = cliente.ventas.exclude(estado="cancelada").order_by("-creado_en")

        total_gastado = sum(v.total for v in ventas)
        n_ventas = len(ventas)
        pagos = (
            PagoFiado.objects.filter(venta__cliente=cliente)
            .select_related("venta", "metodo_pago")
            .order_by("-creado_en")
        )
        pagado_fiado = sum(p.cantidad for p in pagos)

        paginador = Paginator(ventas, 15)
        pagina = self.request.GET.get("pagina")
        context.update(
            {
                "n_ventas": n_ventas,
                "total_gastado": total_gastado,
                "ticket_medio": (total_gastado / n_ventas) if n_ventas else 0,
                "ultima_visita": ventas[0].creado_en if n_ventas else None,
                "saldo_fiado": cliente.saldo_fiado,
                "pagado_fiado": pagado_fiado,
                "ventas_pagina": paginador.get_page(pagina),
                "pagos": pagos[:10],
            }
        )
        return context
