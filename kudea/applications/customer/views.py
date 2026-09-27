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

    from .forms import ClienteFiadoForm

    return render(request, "customer/fiado.html", {
        "ventas": ventas,
        "deudores": deudores,
        "q": q,
        "form": ClienteFiadoForm(),
        "total_por_cobrar": sum(v.pendiente_fiado for v in ventas),
        "metodos_pago": MetodoPago.objects.filter(activo=True).exclude(
            nombre__iexact="Fiado"
        ),
    })


@require_POST
@login_required
def fiado_cobrar(request, venta_id):
    """Cobro total o parcial de un ticket → el dinero SÍ entra en caja."""
    from applications.cashflow.models import Cuenta, Movimiento
    from applications.cashflow.services import register_movement

    venta = get_object_or_404(Venta, pk=venta_id)
    pendiente = venta.pendiente_fiado

    try:
        cantidad = Decimal(str(request.POST.get("cantidad", "0") or "0"))
    except Exception:
        cantidad = Decimal("0")

    if cantidad <= 0:
        messages.error(request, "El importe debe ser mayor que 0.")
        return redirect("fiado_lista")
    if cantidad > pendiente:
        messages.error(request, f"Sólo falta cobrar {pendiente} € de ese ticket.")
        return redirect("fiado_lista")

    metodo = MetodoPago.objects.filter(id=request.POST.get("metodo_pago")).first()
    es_efectivo = (not metodo) or metodo.nombre.lower() in ("efectivo", "cash", "fiado")
    cuenta, _ = Cuenta.objects.get_or_create(nombre="Caja" if es_efectivo else "Banco")

    with transaction.atomic():
        pago = PagoFiado.objects.create(
            venta=venta,
            cantidad=cantidad,
            metodo_pago=metodo,
            usuario=request.user,
        )
        # El dinero entra en caja en el momento del cobro (antes: no estaba)
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

    return redirect("fiado_recibo", pago_id=pago.id)


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
    })


# ------------------------------------------------------------
#  ALTA DE CLIENTE DESDE EL FIADO (formulario propio e
#  independiente del que usa tpv_shop)
# ------------------------------------------------------------
from .forms import ClienteFiadoForm


@login_required
def fiado_cliente_nuevo(request):
    """Alta de cliente: normal (redirect) o AJAX desde el popup de /fiado/."""
    es_ajax = request.headers.get("x-requested-with") == "XMLHttpRequest"

    if request.method == "POST":
        form = ClienteFiadoForm(request.POST)
        if form.is_valid():
            cliente = form.save()
            if es_ajax:
                return JsonResponse(
                    {"ok": True, "id": cliente.id, "nombre": cliente.nombre}
                )
            messages.success(
                request,
                f"Cliente «{cliente.nombre}» creado. Ya puedes venderle a fiado.",
            )
            return redirect("fiado_lista")
        if es_ajax:
            return JsonResponse(
                {"ok": False, "errors": form.errors.get_json_data()},
                status=400,
            )
        messages.error(request, "Revisa los datos del formulario.")
    else:
        form = ClienteFiadoForm()

    return render(request, "customer/fiado_nuevo_cliente.html", {"form": form})


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
