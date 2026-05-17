# ============================
# Django imports
# ============================
import os

from django.shortcuts import render, redirect
from django.conf import settings
from django.http import JsonResponse, HttpResponse
from django.views.generic import TemplateView, CreateView, ListView, View
from django.urls import reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import transaction, models
from django.utils.text import slugify
from django.template.loader import render_to_string
from django.core.paginator import Paginator
from django.db.models import Q, Sum, Count, F
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_protect
from django.utils.timezone import localdate

import json
from datetime import datetime, timedelta, date
from decimal import Decimal  # 👈 AÑADIR
import random
import string

# ============================
# Proyecto imports
# ============================
from .models import Producto, Venta, DetalleVenta, Categoria
from applications.config.models import ConfiguracionFiscal
from applications.payments.models import MetodoPago
from applications.product.forms import ProductoForm

# ============================
# CashFlow and Cash imports 👇
# ============================
from applications.cashflow.models import Cuenta, Movimiento
from applications.cashflow.services import register_movement
from applications.cash.models import AperturaCaja


def _parse_sale_items(items):
    parsed_items = []

    for raw_item in items:
        product_id = raw_item.get("id") or raw_item.get("producto_id")
        cantidad = int(raw_item.get("cantidad", 0))

        if cantidad <= 0:
            raise ValueError("La cantidad debe ser mayor que cero")

        producto = Producto.objects.select_for_update().get(pk=product_id)
        # Omitido para permitir ventas con stock negativo (solo modo aviso en frontend)
        # if producto.stock < cantidad:
        #     raise ValueError(f"Stock insuficiente para {producto.nombre}")

        unit_price = Decimal(str(raw_item.get("precio", producto.precio)))
        parsed_items.append({
            "producto": producto,
            "cantidad": cantidad,
            "precio": unit_price,
            "total": unit_price * cantidad,
        })

    return parsed_items


def _cashflow_payment_data(metodo_pago):
    nombre = (metodo_pago.nombre or "").strip().lower()

    if any(token in nombre for token in ["efectivo", "cash", "metalic", "metálic"]):
        return "Caja", Movimiento.MetodoPago.EFECTIVO

    if "bizum" in nombre:
        return "Banco", Movimiento.MetodoPago.BIZUM

    if any(token in nombre for token in ["tarjeta", "card", "visa", "mastercard", "datáfono", "datafono"]):
        return "Banco", Movimiento.MetodoPago.TARJETA

    if any(token in nombre for token in ["transfer", "banco", "bank"]):
        return "Banco", Movimiento.MetodoPago.TRANSFERENCIA

    return "Banco", Movimiento.MetodoPago.EFECTIVO if metodo_pago.acepta_cambio else Movimiento.MetodoPago.TRANSFERENCIA


# ============================================================
# HOME
# ============================================================

class HomePageView(LoginRequiredMixin, ListView):
    template_name = 'home/index.html'
    model = Producto
    context_object_name = 'productos'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        from django.db.models import Sum, Count
        from django.utils.timezone import localdate
        from applications.home.models import Venta
        
        hoy = localdate()
        
        # Estadísticas del día
        ventas_hoy = Venta.objects.filter(creado_en__date=hoy, estado="completada")
        context['ventas_total_hoy'] = ventas_hoy.aggregate(total=Sum('total'))['total'] or 0
        context['ventas_count_hoy'] = ventas_hoy.count()
        
        # Productos totales
        context['total_productos'] = Producto.objects.filter(activo=True).count()
        
        # Actividad reciente (últimas 10 ventas)
        context['actividad_reciente'] = Venta.objects.all().select_related('usuario', 'metodo_pago').order_by('-creado_en')[:10]
        
        # Comunicaciones
        from applications.home.models import Comunicacion
        comunicaciones = Comunicacion.objects.all()[:20]
        context['comunicaciones'] = comunicaciones
        context['unread_comms'] = Comunicacion.objects.exclude(visto_por=self.request.user).count()

        return context

# ============================================================
# TPV GENERAL
# ============================================================

class TpvGeneralView(LoginRequiredMixin, TemplateView):
    template_name = 'home/tpv_general.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['productos'] = Producto.objects.filter(activo=True).order_by('nombre')
        context['categorias'] = Categoria.objects.all().order_by('nombre')
        context['metodos_pago2'] = MetodoPago.objects.filter(activo=True)
        context['config'] = ConfiguracionFiscal.objects.first()
        # Balance del día
        hoy = localdate()
        apertura = AperturaCaja.objects.filter(usuario=self.request.user, fecha=hoy, estado="abierta").first()
        fondo = apertura.fondo_inicial if apertura else 0
        ventas_hoy = Venta.objects.filter(usuario=self.request.user, creado_en__date=hoy, estado="completada").aggregate(total=models.Sum("total"))["total"] or 0
        context["balance_caja"] = fondo + ventas_hoy
        context["caja_abierta"] = apertura is not None
        context['current_user'] = self.request.user
        return context

class KudeaLandingPageView(TemplateView):
    template_name = 'home/kudea_landing.html'

class TPVView(LoginRequiredMixin, TemplateView):
    template_name = 'home/index.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['productos'] = Producto.objects.filter(activo=True).order_by('nombre')
        context['categorias'] = Categoria.objects.all().order_by('nombre')
        context['metodos_pago2'] = MetodoPago.objects.filter(activo=True)
        context['config'] = ConfiguracionFiscal.objects.first()
        context['current_user'] = self.request.user
        return context

# ============================================================
# CREAR CATEGORÍA AJAX
# ============================================================

class CrearCategoriaAjaxView(LoginRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        data = json.loads(request.body)
        nombre = data.get("nombre")
        descripcion = data.get("descripcion", "")

        if not nombre:
            return JsonResponse({"success": False, "error": "Nombre requerido"}, status=400)

        if Categoria.objects.filter(nombre__iexact=nombre).exists():
            return JsonResponse({"success": False, "error": "Ya existe una categoría con ese nombre"}, status=400)

        categoria = Categoria.objects.create(nombre=nombre, descripcion=descripcion, slug=slugify(nombre))
        return JsonResponse({"success": True, "id": categoria.id, "nombre": categoria.nombre})

# ============================================================
# PROCESAR VENTA
# ============================================================

class ProcesarVentaView(LoginRequiredMixin, CreateView):
    model = Venta
    fields = []
    success_url = reverse_lazy('home')

    @transaction.atomic
    def post(self, request, *args, **kwargs):
        try:
            data = json.loads(request.body)
            items = _parse_sale_items(data['items'])

            venta = Venta(
                usuario=request.user,
                metodo_pago_id=data['metodo_pago_id'],
                subtotal=data['subtotal'],
                iva=data['iva'],
                total=data['total'],
                recibido=data.get('recibido', 0),
                cambio=data.get('cambio', 0)
            )
            venta.save()

            for item in items:
                producto = item['producto']
                DetalleVenta.objects.create(
                    venta=venta,
                    producto=producto,
                    cantidad=item['cantidad'],
                    precio_unitario=item['precio'],
                    total=item['total']
                )

                producto.stock -= item['cantidad']
                producto.save(update_fields=['stock'])

            return JsonResponse({
                'success': True,
                'venta_id': venta.id,
                'codigo_venta': venta.codigo
            })

        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=400)

# ============================================================
# LISTA PRODUCTOS
# ============================================================

class ProductoListView(LoginRequiredMixin, ListView):
    model = Producto
    template_name = 'home/product_list.html'
    context_object_name = 'productos'
    paginate_by = 20

    def get_queryset(self):
        queryset = super().get_queryset().filter(activo=True)
        search = self.request.GET.get('search', '')
        categoria_id = self.request.GET.get('categoria_id', None)
        stock_bajo = self.request.GET.get('stock_bajo', None)

        if search:
            queryset = queryset.filter(
                models.Q(nombre__icontains=search) |
                models.Q(codigo_barras__icontains=search)
            )

        if categoria_id and categoria_id != '0':
            queryset = queryset.filter(categoria_id=categoria_id)

        if stock_bajo == 'true':
            queryset = queryset.filter(stock__lt=models.F('stock_minimo'))

        return queryset.order_by('nombre')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Use the queryset already filtered by get_queryset() to ensure stats match the displayed list
        queryset = self.get_queryset()
        
        context['categorias'] = Categoria.objects.all()
        context['total_products'] = queryset.count()
        
        # Count items with stock < stock_minimo in the current list
        context['low_stock_count'] = queryset.filter(
            stock__lt=models.F('stock_minimo')
        ).count()

        # Calculate Total Inventory Value and totals per product
        total_val = 0
        for p in queryset:
            p.total_por_producto = p.stock * p.precio
            if p.stock > 0:
                total_val += p.total_por_producto
        
        context['total_inventory_value'] = total_val
        context['productos'] = queryset # Ensure we use the same list with added attribute
        
        # For the print report: Get ALL products (not paginated) and group them
        # We use the filtered queryset but without pagination
        full_queryset = self.get_queryset()
        context['all_products'] = full_queryset
        
        return context

# ============================================================
# CREAR PRODUCTO
# ============================================================

class CrearProductoView(LoginRequiredMixin, CreateView):
    model = Producto
    form_class = ProductoForm
    template_name = 'home/crear_producto.html'

    def get_object(self, queryset=None):
        pk = self.request.GET.get('id')
        if pk:
            return Producto.objects.filter(pk=pk).first()
        return None

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        instance = self.get_object()
        if instance:
            kwargs['instance'] = instance
        return kwargs

    def get_initial(self):
        initial = super().get_initial()
        instance = self.get_object()
        if not instance:
            # Generar código automático solo para nuevos productos
            while True:
                new_code = 'KUD-' + ''.join(random.choices(string.digits, k=8))
                if not Producto.objects.filter(codigo_barras=new_code).exists():
                    initial['codigo_barras'] = new_code
                    break
        return initial

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['is_edit'] = self.get_object() is not None
        return context

    def form_valid(self, form):
        # El form.save() manejará tanto el insert como el update ya que instance está seteado
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy('home_app:lista_productos')

# ============================================================
# ⭐ VISTA ANTIGUA — VentasListView
# ============================================================

class VentasListView(LoginRequiredMixin, ListView):
    model = Venta
    template_name = 'home/ventas.html'   # Plantilla antigua
    context_object_name = 'ventas'
    paginate_by = 20
    ordering = ['-creado_en']

# ============================================================
# NUEVA VISTA: HISTORIAL COMPLETO DE VENTAS (FILTROS)
# ============================================================

class HistorialVentasView(LoginRequiredMixin, View):
    template_name = "home/ventas_list.html"

    def get(self, request):

        # -------------------------
        # Recibir los filtros GET
        # -------------------------
        q = request.GET.get("q", "").strip()
        fecha = request.GET.get("fecha", "").strip()
        metodo = request.GET.get("metodo", "").strip()

        # -------------------------
        # Query base
        # -------------------------
        ventas = Venta.objects.all().select_related(
            "metodo_pago", "usuario"
        ).order_by("-creado_en")

        # -------------------------
        # Filtrar por texto (código, usuario, método)
        # -------------------------
        if q:
            ventas = ventas.filter(
                Q(codigo__icontains=q) |
                Q(usuario__username__icontains=q) |
                Q(metodo_pago__nombre__icontains=q)
            )

        # -------------------------
        # Filtrar por fecha exacta
        # -------------------------
        if fecha:
            ventas = ventas.filter(creado_en__date=fecha)

        # -------------------------
        # Filtrar por método de pago
        # -------------------------
        if metodo:
            ventas = ventas.filter(metodo_pago_id=metodo)

        # -------------------------
        # Paginación
        # -------------------------
        paginator = Paginator(ventas, 15)
        page_number = request.GET.get("page")
        page_obj = paginator.get_page(page_number)

        # -------------------------
        # Estadísticas globales (no afectadas por filtros de paginación)
        # -------------------------
        from django.utils import timezone
        from django.db.models import Sum

        hoy = timezone.now().date()
        total_ventas_count = Venta.objects.count()
        facturado_hoy = Venta.objects.filter(
            creado_en__date=hoy
        ).aggregate(total=Sum('total'))['total'] or 0

        # -------------------------
        # Contexto enviado al template
        # -------------------------
        context = {
            "title": "Historial de Tickets",
            "ventas": page_obj,
            "page_obj": page_obj,
            "is_paginated": page_obj.has_other_pages(),
            "metodos": MetodoPago.objects.filter(activo=True),
            "request": request,
            "total_ventas_count": total_ventas_count,
            "facturado_hoy": facturado_hoy,
        }

        return render(request, self.template_name, context)


# ============================================================
# VENTA DETALLE
# ============================================================

class VentaDetalleView(LoginRequiredMixin, TemplateView):
    template_name = 'home/venta_detalle.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        venta = Venta.objects.get(pk=self.kwargs['pk'])
        detalles = venta.detalles.all()
        
        # Calcular desglose de IVA y Totales Reales
        iva_breakdown = {}
        total_items = 0
        
        for d in detalles:
            rate = float(d.producto.porcentaje_iva or 21)
            item_total = float(d.total)
            total_items += item_total
            
            # Desglosamos: Base = Total / (1 + (IVA/100))
            base = item_total / (1 + (rate / 100))
            cuota = item_total - base
            
            if rate not in iva_breakdown:
                iva_breakdown[rate] = {'base': 0, 'cuota': 0}
            
            iva_breakdown[rate]['base'] += base
            iva_breakdown[rate]['cuota'] += cuota

        # Usar los totales y cambios exactos registrados en la base de datos
        total_final = float(venta.total)
        cambio_real = float(venta.cambio or 0)

        # Parsear desglose de Pago Mixto si aplica
        desglose_mixto = None
        if venta.metodo_pago.nombre == "Pago Mixto" and venta.notas:
            try:
                import json
                desglose_mixto = json.loads(venta.notas)
            except Exception:
                pass

        context.update({
            'venta': venta,
            'detalles': detalles,
            'iva_breakdown': iva_breakdown,
            'total_real': total_final,
            'subtotal_real': total_items - float(venta.iva or 0), # Aproximado para la base
            'cambio_real': cambio_real,
            'desglose_mixto': desglose_mixto,
            'config': ConfiguracionFiscal.objects.first()
        })
        return context

    def get_template_names(self):
        fmt = self.request.GET.get('format')
        if fmt == 'ticket':
            return ['home/venta_ticket_pos.html']
        elif fmt == 'reverso':
            return ['home/venta_ticket_reverso.html']
        return [self.template_name]


# ============================================================
# API PRODUCTOS
# ============================================================

def obtener_productos(request):
    if request.method == 'GET':
        search = request.GET.get('search', '')
        categoria_id = request.GET.get('categoria_id', None)

        productos = Producto.objects.filter(activo=True)

        if search:
            productos = productos.filter(
                models.Q(nombre__icontains=search) |
                models.Q(codigo_barras__icontains=search)
            )

        if categoria_id and categoria_id != '0':
            productos = productos.filter(categoria_id=categoria_id)

        productos = productos.order_by('nombre')[:50]

        data = [{
            'id': p.id,
            'nombre': p.nombre,
            'precio': float(p.precio),
            'categoria': p.categoria.nombre if p.categoria else '',
            'stock': p.stock,
            'codigo_barras': p.codigo_barras or ''
        } for p in productos]

        return JsonResponse(data, safe=False)

    return JsonResponse({'error': 'Método no permitido'}, status=405)


# ============================================================
# REPORTES
# ============================================================

def reporte_ventas(request):
    if request.method == 'GET':
        from datetime import date, timedelta
        from django.db.models import Sum

        hoy = date.today()

        # ========= HOY =========
        ayer = hoy - timedelta(days=1)

        ventas_hoy = Venta.objects.filter(
            creado_en__date=hoy,
            estado='completada'
        )

        ventas_ayer = Venta.objects.filter(
            creado_en__date=ayer,
            estado='completada'
        )

        total_hoy = ventas_hoy.aggregate(Sum('total'))['total__sum'] or 0
        total_ayer = ventas_ayer.aggregate(Sum('total'))['total__sum'] or 0

        productos_hoy = DetalleVenta.objects.filter(
            venta__in=ventas_hoy
        ).aggregate(Sum('cantidad'))['cantidad__sum'] or 0

        productos_ayer = DetalleVenta.objects.filter(
            venta__in=ventas_ayer
        ).aggregate(Sum('cantidad'))['cantidad__sum'] or 0

        # ========= SEMANA =========
        inicio_semana = hoy - timedelta(days=hoy.weekday())
        inicio_semana_pasada = inicio_semana - timedelta(days=7)
        fin_semana_pasada = inicio_semana - timedelta(days=1)

        ventas_semana = Venta.objects.filter(
            creado_en__date__gte=inicio_semana,
            estado='completada'
        )

        ventas_semana_pasada = Venta.objects.filter(
            creado_en__date__gte=inicio_semana_pasada,
            creado_en__date__lte=fin_semana_pasada,
            estado='completada'
        )

        total_semana = ventas_semana.aggregate(Sum('total'))['total__sum'] or 0
        total_semana_pasada = ventas_semana_pasada.aggregate(Sum('total'))['total__sum'] or 0

        productos_semana = DetalleVenta.objects.filter(
            venta__in=ventas_semana
        ).aggregate(Sum('cantidad'))['cantidad__sum'] or 0

        productos_semana_pasada = DetalleVenta.objects.filter(
            venta__in=ventas_semana_pasada
        ).aggregate(Sum('cantidad'))['cantidad__sum'] or 0

        # ========= MES =========
        inicio_mes = hoy.replace(day=1)
        if inicio_mes.month == 1:
            inicio_mes_pasado = inicio_mes.replace(year=inicio_mes.year - 1, month=12)
        else:
            inicio_mes_pasado = inicio_mes.replace(month=inicio_mes.month - 1)

        fin_mes_pasado = inicio_mes - timedelta(days=1)

        ventas_mes = Venta.objects.filter(
            creado_en__date__gte=inicio_mes,
            estado='completada'
        )

        ventas_mes_pasado = Venta.objects.filter(
            creado_en__date__gte=inicio_mes_pasado,
            creado_en__date__lte=fin_mes_pasado,
            estado='completada'
        )

        total_mes = ventas_mes.aggregate(Sum('total'))['total__sum'] or 0
        total_mes_pasado = ventas_mes_pasado.aggregate(Sum('total'))['total__sum'] or 0

        productos_mes = DetalleVenta.objects.filter(
            venta__in=ventas_mes
        ).aggregate(Sum('cantidad'))['cantidad__sum'] or 0

        productos_mes_pasado = DetalleVenta.objects.filter(
            venta__in=ventas_mes_pasado
        ).aggregate(Sum('cantidad'))['cantidad__sum'] or 0

        return JsonResponse({
            "hoy": {
                "total": float(total_hoy),
                "ventas": ventas_hoy.count(),
                "productos": productos_hoy,
                "productos_anterior": productos_ayer
            },
            "semana": {
                "total": float(total_semana),
                "ventas": ventas_semana.count(),
                "productos": productos_semana,
                "productos_anterior": productos_semana_pasada
            },
            "mes": {
                "total": float(total_mes),
                "ventas": ventas_mes.count(),
                "productos": productos_mes,
                "productos_anterior": productos_mes_pasado
            }
        })

    return JsonResponse({'error': 'Método no permitido'}, status=405)

# ============================================================
# GUARDAR VENTA (IVA DINÁMICO + CASHFLOW + DECIMAL CORRECTO)
# ============================================================

from decimal import Decimal
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_protect
from django.http import JsonResponse
from django.db import transaction
import json

@require_POST
@csrf_protect
@transaction.atomic
def guardar_venta(request):

    print("🚀 guardar_venta EJECUTADA")

    if not request.user.is_authenticated:
        return JsonResponse({
            "success": False,
            "code": "AUTH_REQUIRED",
            "error": "Debes iniciar sesión para guardar la venta."
        }, status=401)

    try:
        data = json.loads(request.body.decode("utf-8"))
        ticket = data.get("ticket", [])
        metodo_pago_id = data.get("metodo_pago")
        recibido = Decimal(str(data.get("recibido", 0)))
        descuento = Decimal(str(data.get("descuento", 0)))
        desglose_mixto = data.get("desglose_mixto")  # 👈 Obtener desglose de Pago Mixto

        if not ticket:
            return JsonResponse({"error": "El ticket está vacío"}, status=400)

        if not metodo_pago_id:
            return JsonResponse({"error": "Método de pago requerido"}, status=400)

        metodo_pago = MetodoPago.objects.get(id=metodo_pago_id)
        parsed_items = _parse_sale_items(ticket)

        # ==========================
        # CÁLCULO FINANCIERO 100% DECIMAL
        # ==========================
        subtotal_bruto = sum(item["total"] for item in parsed_items)

        tasa_descuento = Decimal("0")
        if subtotal_bruto > Decimal("0") and descuento > Decimal("0"):
            tasa_descuento = descuento / subtotal_bruto

        iva = Decimal("0")
        for item in parsed_items:
            producto = item["producto"]
            item_bruto = item["total"]
            item_neto = item_bruto * (Decimal("1") - tasa_descuento)
            
            p_iva = getattr(producto, 'porcentaje_iva', Decimal("21"))
            if not p_iva: 
                p_iva = Decimal("21")
                
            item_iva = item_neto * (Decimal(p_iva) / Decimal("100"))
            iva += item_iva

        # subtotal es el bruto que se registra en Venta
        subtotal = subtotal_bruto
        total = subtotal - descuento + iva
        cambio = recibido - total

        print("💰 Subtotal:", subtotal)
        print("💰 IVA Total:", iva)
        print("💰 Total:", total)

        # ==========================
        # PREPARAR NOTAS (SERIALIZACIÓN DEL DESGLOSE MIXTO)
        # ==========================
        notas_guardar = None
        if desglose_mixto and metodo_pago.nombre == "Pago Mixto":
            notas_guardar = json.dumps(desglose_mixto)

        # ==========================
        # CREAR VENTA
        # ==========================
        venta = Venta.objects.create(
            usuario=request.user,
            metodo_pago=metodo_pago,
            subtotal=subtotal,
            descuento=descuento,
            iva=iva,
            total=total,
            recibido=recibido,
            cambio=cambio,
            estado="completada",
            notas=notas_guardar,
        )

        print("✅ Venta creada:", venta.id)

        # ==========================
        # CREAR DETALLES Y ACTUALIZAR STOCK
        # ==========================
        for item in parsed_items:
            producto = item["producto"]
            cantidad = item["cantidad"]
            precio = item["precio"]

            DetalleVenta.objects.create(
                venta=venta,
                producto=producto,
                cantidad=cantidad,
                precio_unitario=precio,
                total=item["total"],
            )

            producto.stock -= cantidad
            producto.save(update_fields=["stock"])

        print("📦 Detalles creados")

        # ==========================================
        # REGISTRAR MOVIMIENTO EN CASHFLOW
        # ==========================================
        try:
            from applications.cashflow.models import Cuenta, Movimiento
            from applications.cashflow.services import register_movement

            # Si es Pago Mixto y tiene desglose, registramos movimientos separados por cada fracción
            if desglose_mixto and metodo_pago.nombre == "Pago Mixto":
                print("📝 Registrando movimientos fragmentados para Pago Mixto...")
                for medio, importe_parcial in desglose_mixto.items():
                    importe_parcial_dec = Decimal(str(importe_parcial))
                    if importe_parcial_dec > 0:
                        try:
                            mp_parcial = MetodoPago.objects.get(nombre__iexact=medio)
                            cuenta_nombre, movimiento_metodo = _cashflow_payment_data(mp_parcial)
                        except MetodoPago.DoesNotExist:
                            cuenta_nombre = "Caja" if medio.lower() == "efectivo" else "Banco"
                            movimiento_metodo = Movimiento.MetodoPago.EFECTIVO if medio.lower() == "efectivo" else Movimiento.MetodoPago.TARJETA
                        
                        cuenta, _ = Cuenta.objects.get_or_create(nombre=cuenta_nombre)
                        register_movement(
                            concepto=f"Venta TPV #{venta.codigo} [Fracción {medio.capitalize()}]",
                            tipo=Movimiento.Tipo.INGRESO,
                            origen=Movimiento.Origen.TPV,
                            cuenta=cuenta,
                            cantidad=importe_parcial_dec,
                            metodo_pago=movimiento_metodo,
                            external_ref=f"tpv:venta:{venta.id}:{medio.lower()}",
                            created_by=request.user,
                        )
            else:
                cuenta_nombre, movimiento_metodo = _cashflow_payment_data(metodo_pago)
                cuenta, _ = Cuenta.objects.get_or_create(nombre=cuenta_nombre)

                register_movement(
                    concepto=f"Venta TPV #{venta.codigo}",
                    tipo=Movimiento.Tipo.INGRESO,
                    origen=Movimiento.Origen.TPV,
                    cuenta=cuenta,
                    cantidad=total,
                    metodo_pago=movimiento_metodo,
                    external_ref=f"tpv:venta:{venta.id}",
                    created_by=request.user,
                )

            print("💚 Movimiento creado con éxito")

        except Exception as e:
            print("❌ ERROR EN CASHFLOW:", str(e))

        return JsonResponse({
            "success": True,
            "venta_id": venta.id,
            "codigo_venta": venta.codigo
        })

    except MetodoPago.DoesNotExist:
        return JsonResponse({"error": "Método de pago inválido"}, status=400)

    except Exception as e:
        print("💥 ERROR GENERAL:", str(e))
        return JsonResponse({
            "success": False,
            "error": str(e)
        }, status=400)



# ======================================================
# 📌 Función utilitaria — Obtener datos de ventas por rango
# ======================================================
def obtener_datos_arqueo_completo(inicio, fin, tipo, usuario, fondo_manual=None):
    """Obtiene el conjunto completo de datos para el reporte profesional."""
    from django.db.models import Sum, Count, F, ExpressionWrapper, FloatField
    from django.db.models.functions import ExtractHour
    from applications.cash.models import AperturaCaja
    from applications.home.models import Venta, DetalleVenta
    from applications.config.models import ConfiguracionFiscal

    # ── Ventas del periodo
    ventas = Venta.objects.filter(
        creado_en__date__gte=inicio,
        creado_en__date__lte=fin,
        estado="completada"
    ).select_related("usuario", "metodo_pago").order_by("creado_en")

    # ── Fondo Inicial (Apertura)
    if fondo_manual is not None:
        fondo_inicial = float(fondo_manual)
    else:
        apertura = AperturaCaja.objects.filter(
            fecha__gte=inicio,
            fecha__lte=fin
        ).order_by("hora_apertura").first()
        
        if apertura:
            fondo_inicial = float(apertura.fondo_inicial)
        else:
            conf = ConfiguracionFiscal.objects.first()
            fondo_inicial = float(conf.fondo_caja_defecto) if conf else 200.00

    # ── Totales generales
    agg = ventas.aggregate(
        total_bruto=Sum("total"),
        total_subtotal=Sum("subtotal"),
        total_iva=Sum("iva"),
        total_descuentos=Sum("descuento"),
        total_recibido=Sum("recibido"),
        total_cambio=Sum("cambio"),
    )
    total_bruto      = float(agg["total_bruto"]      or 0)
    total_subtotal   = float(agg["total_subtotal"]   or 0)
    total_iva        = float(agg["total_iva"]        or 0)
    total_descuentos = float(agg["total_descuentos"] or 0)
    total_recibido   = float(agg["total_recibido"]   or 0)
    total_cambio     = float(agg["total_cambio"]     or 0)
    total_tickets    = ventas.count()
    ticket_medio     = round(total_bruto / total_tickets, 2) if total_tickets else 0

    # Cuadre
    total_efectivo_neto = total_recibido - total_cambio
    total_no_efectivo    = total_bruto - total_efectivo_neto
    total_esperado       = float(fondo_inicial) + total_efectivo_neto

    # ── Coste y beneficio
    detalles = DetalleVenta.objects.filter(venta__in=ventas).annotate(
        coste_linea=ExpressionWrapper(
            F("cantidad") * F("producto__costo"),
            output_field=FloatField()
        )
    )
    total_coste = float(detalles.aggregate(t=Sum("coste_linea"))["t"] or 0)
    beneficio_bruto = total_subtotal - total_coste
    margen = round((beneficio_bruto / total_subtotal * 100), 2) if total_subtotal else 0

    # ── Desglose por método de pago (con soporte inteligente para Pago Mixto)
    desglose_pagos = {}
    tickets_por_metodo = {}

    for v in ventas:
        if v.metodo_pago.nombre == "Pago Mixto" and v.notas:
            try:
                import json
                desglose_json = json.loads(v.notas)
                for medio, importe_parcial in desglose_json.items():
                    medio_display = medio.capitalize()
                    val = float(importe_parcial)
                    if val > 0:
                        desglose_pagos[medio_display] = desglose_pagos.get(medio_display, 0.0) + val
                        if medio_display not in tickets_por_metodo:
                            tickets_por_metodo[medio_display] = set()
                        tickets_por_metodo[medio_display].add(v.id)
            except Exception:
                m_nombre = v.metodo_pago.nombre
                desglose_pagos[m_nombre] = desglose_pagos.get(m_nombre, 0.0) + float(v.total)
                if m_nombre not in tickets_por_metodo:
                    tickets_por_metodo[m_nombre] = set()
                tickets_por_metodo[m_nombre].add(v.id)
        else:
            m_nombre = v.metodo_pago.nombre
            desglose_pagos[m_nombre] = desglose_pagos.get(m_nombre, 0.0) + float(v.total)
            if m_nombre not in tickets_por_metodo:
                tickets_por_metodo[m_nombre] = set()
            tickets_por_metodo[m_nombre].add(v.id)

    por_metodo = []
    for m_nombre, importe in desglose_pagos.items():
        por_metodo.append({
            "metodo_pago__nombre": m_nombre,
            "importe": float(importe),
            "n_tickets": len(tickets_por_metodo.get(m_nombre, []))
        })
    por_metodo = sorted(por_metodo, key=lambda x: x["importe"], reverse=True)

    # ── Desglose por cajero
    por_cajero = (
        ventas.values("usuario__username", "usuario__first_name", "usuario__last_name")
        .annotate(importe=Sum("total"), n_tickets=Count("id"))
        .order_by("-importe")
    )
    for c in por_cajero:
        c["importe"] = float(c["importe"] or 0)
        nombre = f"{c['usuario__first_name']} {c['usuario__last_name']}".strip()
        c["nombre_display"] = nombre if nombre else c["usuario__username"]

    # ── Top 10 productos
    top_productos = (
        detalles.values("producto__nombre")
        .annotate(unidades=Sum("cantidad"), ingresos=Sum("total"))
        .order_by("-unidades")[:10]
    )
    for p in top_productos:
        p["ingresos"] = float(p["ingresos"] or 0)

    # ── Incidencias
    ventas_anuladas = Venta.objects.filter(creado_en__date__gte=inicio, creado_en__date__lte=fin, estado="cancelada").count()
    ventas_pendientes = Venta.objects.filter(creado_en__date__gte=inicio, creado_en__date__lte=fin, estado="pendiente").count()

    # ── Desglose de IVA por Tipo (4%, 10%, 21%, etc)
    from django.db.models import F, DecimalField, ExpressionWrapper, Value
    iva_desglose = (
        detalles.values("producto__porcentaje_iva")
        .annotate(
            base_total=Sum(ExpressionWrapper(F("total") / (Value(1.0) + (F("producto__porcentaje_iva") / Value(100.0))), output_field=DecimalField(max_digits=10, decimal_places=2))),
            iva_total=Sum(ExpressionWrapper(F("total") - (F("total") / (Value(1.0) + (F("producto__porcentaje_iva") / Value(100.0)))), output_field=DecimalField(max_digits=10, decimal_places=2)))
        )
        .order_by("-producto__porcentaje_iva")
    )
    for iva in iva_desglose:
        iva["porcentaje"] = float(iva["producto__porcentaje_iva"])
        iva["base"] = float(iva["base_total"] or 0)
        iva["cuota"] = float(iva["iva_total"] or 0)

    return {
        "tipo": tipo.title(),
        "fecha_inicio": inicio,
        "fecha_fin": fin,
        "ventas": ventas,
        "usuario": usuario,
        "total_tickets": total_tickets,
        "total_bruto": total_bruto,
        "total_subtotal": total_subtotal,
        "total_iva": total_iva,
        "total_descuentos": total_descuentos,
        "total_recibido": total_recibido,
        "total_cambio": total_cambio,
        "ticket_medio": ticket_medio,
        "total_coste": total_coste,
        "beneficio_bruto": beneficio_bruto,
        "margen": margen,
        "por_metodo": por_metodo,
        "por_cajero": por_cajero,
        "top_productos": top_productos,
        "fondo_inicial": fondo_inicial,
        "ventas_anuladas": ventas_anuladas,
        "ventas_pendientes": ventas_pendientes,
        "total_efectivo_neto": total_efectivo_neto,
        "total_esperado": total_esperado,
        "iva_desglose": iva_desglose,
    }

def obtener_resumen_ventas(inicio, fin):
    """Versión simplificada para compatibilidad o dashboards rápidos."""
    ventas = Venta.objects.filter(
        creado_en__date__gte=inicio,
        creado_en__date__lte=fin,
        estado="completada"
    )

    total_ventas = ventas.aggregate(Sum('total'))['total__sum'] or 0
    total_subtotal = ventas.aggregate(Sum('subtotal'))['subtotal__sum'] or 0
    total_iva = ventas.aggregate(Sum('iva'))['iva__sum'] or 0
    cantidad_tickets = ventas.count()

    # Totales por método de pago
    metodos = ventas.values("metodo_pago__nombre").annotate(
        total=Sum("total"),
        cantidad=Count("id")
    )

    # Totales por productos
    productos = DetalleVenta.objects.filter(
        venta__in=ventas
    ).values("producto__nombre").annotate(
        cantidad=Sum("cantidad"),
        total=Sum("total")
    ).order_by("-cantidad")

    return {
        "total_ventas": total_ventas,
        "total_subtotal": total_subtotal,
        "total_iva": total_iva,
        "cantidad_tickets": cantidad_tickets,
        "metodos": list(metodos),
        "productos": list(productos),
        "ventas": ventas,
    }


def registrar_cierre_desde_rango(request, tipo, fecha_inicio, fecha_fin):
    """Función utilitaria para guardar un registro de CierreCaja."""
    from applications.cash.models import CierreCaja, AperturaCaja
    from applications.config.models import ConfiguracionFiscal
    from django.db.models import Sum
    from django.utils import timezone
    from django.contrib import messages

    hoy = timezone.localdate()
    ventas = Venta.objects.filter(
        creado_en__date__gte=fecha_inicio,
        creado_en__date__lte=fecha_fin,
        estado="completada"
    )

    apertura = AperturaCaja.objects.filter(
        fecha__gte=fecha_inicio,
        fecha__lte=fecha_fin
    ).order_by("hora_apertura").first()

    if apertura:
        fondo_inicial = float(apertura.fondo_inicial)
    else:
        conf = ConfiguracionFiscal.objects.first()
        fondo_inicial = float(conf.fondo_caja_defecto) if conf else 200.00

    agg = ventas.aggregate(
        total_bruto=Sum("total"),
        total_recibido=Sum("recibido"),
        total_cambio=Sum("cambio"),
    )
    total_bruto = float(agg["total_bruto"] or 0)
    total_recibido = float(agg["total_recibido"] or 0)
    total_cambio = float(agg["total_cambio"] or 0)
    
    total_efectivo_neto = total_recibido - total_cambio
    total_esperado = fondo_inicial + total_efectivo_neto

    cierre, created = CierreCaja.objects.update_or_create(
        tipo=tipo,
        fecha_inicio=fecha_inicio,
        fecha_fin=fecha_fin,
        defaults={
            'fecha': hoy,
            'usuario': request.user,
            'fondo_inicial': fondo_inicial,
            'efectivo_esperado': total_esperado,
            'efectivo_retirado': total_efectivo_neto,
            'total_ventas': total_bruto,
        }
    )
    
    # Cerrar la sesión de caja (AperturaCaja)
    apertura_activa = AperturaCaja.objects.filter(estado='abierta').first()
    if apertura_activa:
        apertura_activa.estado = 'cerrada'
        apertura_activa.hora_cierre = timezone.now()
        apertura_activa.save()
        messages.success(request, f"Cierre de caja ({tipo.capitalize()}) registrado y sesión cerrada con éxito.")
    else:
        messages.success(request, f"Cierre de caja ({tipo.capitalize()}) registrado con éxito.")
    
    return cierre

# ======================================================
# 📌 Menú principal de arqueos
# ======================================================
class ArqueoMenuView(LoginRequiredMixin, TemplateView):
    template_name = "home/arqueo_menu.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        from applications.cash.models import CierreCaja
        context['ultimos_cierres'] = CierreCaja.objects.all().order_by('-fecha', '-hora_cierre')[:10]
        return context


# ======================================================
# 📌 Arqueo diario
# ======================================================
class ArqueoDiarioView(LoginRequiredMixin, TemplateView):
    template_name = "home/arqueo_pdf.html"

    def get_context_data(self, **kwargs):
        hoy = date.today()
        return obtener_datos_arqueo_completo(hoy, hoy, "diario", self.request.user)

    def post(self, request, *args, **kwargs):
        hoy = date.today()
        registrar_cierre_desde_rango(request, "diario", hoy, hoy)
        return redirect(request.path)


# ======================================================
# 📌 Arqueo semanal
# ======================================================
class ArqueoSemanalView(LoginRequiredMixin, TemplateView):
    template_name = "home/arqueo_pdf.html"

    def get_context_data(self, **kwargs):
        hoy = date.today()
        inicio = hoy - timedelta(days=hoy.weekday())
        return obtener_datos_arqueo_completo(inicio, hoy, "semanal", self.request.user)

    def post(self, request, *args, **kwargs):
        hoy = date.today()
        inicio = hoy - timedelta(days=hoy.weekday())
        registrar_cierre_desde_rango(request, "semanal", inicio, hoy)
        return redirect(request.path)


# ======================================================
# 📌 Arqueo mensual
# ======================================================
class ArqueoMensualView(LoginRequiredMixin, TemplateView):
    template_name = "home/arqueo_pdf.html"

    def get_context_data(self, **kwargs):
        hoy = date.today()
        inicio = hoy.replace(day=1)
        return obtener_datos_arqueo_completo(inicio, hoy, "mensual", self.request.user)

    def post(self, request, *args, **kwargs):
        hoy = date.today()
        inicio = hoy.replace(day=1)
        registrar_cierre_desde_rango(request, "mensual", inicio, hoy)
        return redirect(request.path)


# ======================================================
# 📌 Arqueo anual
# ======================================================
class ArqueoAnualView(LoginRequiredMixin, TemplateView):
    template_name = "home/arqueo_pdf.html"

    def get_context_data(self, **kwargs):
        hoy = date.today()
        inicio = hoy.replace(month=1, day=1)
        return obtener_datos_arqueo_completo(inicio, hoy, "anual", self.request.user)

    def post(self, request, *args, **kwargs):
        hoy = date.today()
        inicio = hoy.replace(month=1, day=1)
        registrar_cierre_desde_rango(request, "anual", inicio, hoy)
        return redirect(request.path)


# ======================================================
# 📌 Arqueo personalizado
# ======================================================
class ArqueoPersonalizadoView(LoginRequiredMixin, TemplateView):
    template_name = "home/arqueo_personalizado.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Permitir pre-llenar fechas desde parámetros GET
        context['inicio_prefill'] = self.request.GET.get('inicio', '')
        context['fin_prefill'] = self.request.GET.get('fin', '')
        return context

    def post(self, request, *args, **kwargs):
        if "inicio" in request.POST and "fin" in request.POST:
            # Viene del formulario de selección de fechas
            inicio_str = request.POST.get("inicio")
            fin_str = request.POST.get("fin")
            fondo_str = request.POST.get("fondo")
            inicio = datetime.strptime(inicio_str, "%Y-%m-%d").date()
            fin = datetime.strptime(fin_str, "%Y-%m-%d").date()
            
            fondo_manual = float(fondo_str) if fondo_str else None

            data = obtener_datos_arqueo_completo(inicio, fin, "personalizado", request.user, fondo_manual=fondo_manual)
            data["fecha_inicio_raw"] = inicio_str
            data["fecha_fin_raw"] = fin_str

            return render(request, "home/arqueo_pdf.html", data)
        else:
            # Es el botón de GUARDAR en el resultado
            inicio_str = request.POST.get("fecha_inicio_raw")
            fin_str = request.POST.get("fecha_fin_raw")
            inicio = datetime.strptime(inicio_str, "%Y-%m-%d").date()
            fin = datetime.strptime(fin_str, "%Y-%m-%d").date()
            
            registrar_cierre_desde_rango(request, "personalizado", inicio, fin)
            return redirect(request.path)


# ======================================================
# 📌 Arqueo PDF (Compatibilidad Retroactiva)
# ======================================================
class ArqueoPDFView(LoginRequiredMixin, View):
    def get(self, request, tipo):
        tipos_validos = ["diario", "semanal", "mensual", "anual"]
        if tipo not in tipos_validos:
            return HttpResponse("Tipo de arqueo no válido", status=400)

        hoy = date.today()
        # Priorizar fechas desde parámetros GET
        get_inicio = request.GET.get('inicio')
        get_fin = request.GET.get('fin')
        get_fondo = request.GET.get('fondo')

        if get_inicio and get_fin:
            inicio = datetime.strptime(get_inicio, "%Y-%m-%d").date()
            fin = datetime.strptime(get_fin, "%Y-%m-%d").date()
            fondo_manual = float(get_fondo) if get_fondo else None
            data = obtener_datos_arqueo_completo(inicio, fin, tipo, request.user, fondo_manual=fondo_manual)
            return render(request, "home/arqueo_pdf.html", data)
        else:
            if tipo == "diario":
                fecha_inicio = hoy
                fecha_fin = hoy
            elif tipo == "semanal":
                fecha_inicio = hoy - timedelta(days=hoy.weekday())
                fecha_fin = hoy
            elif tipo == "mensual":
                fecha_inicio = hoy.replace(day=1)
                fecha_fin = hoy
            else:
                fecha_inicio = hoy.replace(month=1, day=1)
                fecha_fin = hoy

        data = obtener_datos_arqueo_completo(fecha_inicio, fecha_fin, tipo, request.user)
        return render(request, "home/arqueo_pdf.html", data)

    def post(self, request, tipo):
        hoy = date.today()
        if tipo == "diario":
            inicio = hoy
        elif tipo == "semanal":
            inicio = hoy - timedelta(days=hoy.weekday())
        elif tipo == "mensual":
            inicio = hoy.replace(day=1)
        else:
            inicio = hoy.replace(month=1, day=1)
        
        registrar_cierre_desde_rango(request, tipo, inicio, hoy)
        return redirect(request.path)


# ============================================================
# FIN DEL ARCHIVO
# ============================================================


# ============================================================
# CENTRO DE AYUDA
# ============================================================

class HelpCenterView(LoginRequiredMixin, TemplateView):
    template_name = 'home/ayuda.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['ayuda_items'] = [
            {
                'id': 'tpv',
                'titulo': 'Ventas y TPV',
                'icono': 'fas fa-cash-register',
                'color': '#3b82f6',
                'descripcion': 'Domina el Punto de Venta: desde la selección de productos hasta el cobro.',
                'guia_completa': [
                    {'paso': 1, 'instruccion': 'Accede al TPV desde el menú lateral clicando en "TPV General".', 'detalles': 'Verás una interfaz limpia con tus categorías de productos en la parte superior.'},
                    {'paso': 2, 'instruccion': 'Selecciona los productos clicando sobre sus tarjetas visuales.', 'detalles': 'Cada clic añadirá una unidad al ticket de la derecha. El sistema sumará los importes automáticamente.'},
                    {'paso': 3, 'instruccion': 'Revisa el ticket.', 'detalles': 'Puedes ajustar cantidades usando los botones (+) y (-) o eliminar un item con el icono de papelera.'},
                    {'paso': 4, 'instruccion': 'Aplica Descuentos si es necesario.', 'detalles': 'Puedes aplicar un descuento general clicando en "Aplicar Descuento" en la barra superior antes de pagar.'},
                    {'paso': 5, 'instruccion': 'Haz clic en el botón "Pagar" (abajo a la derecha).', 'detalles': 'Se abrirá la pantalla de cobro. Aquí puedes elegir Efectivo, Tarjeta, etc.'},
                    {'paso': 6, 'instruccion': 'Finaliza la venta.', 'detalles': 'Haz clic en "Completar Venta" para imprimir el ticket y actualizar el stock instantáneamente.'},
                ],
                'notas_importantes': [
                    'Los precios en el TPV ya muestran el IVA incluido.',
                    'Puedes ver el historial de ventas del día clicando en "Historial" en la barra superior.'
                ]
            },
            {
                'id': 'caja',
                'titulo': 'Control de Caja',
                'icono': 'fas fa-vault',
                'color': '#10b981',
                'descripcion': 'Apertura, cierre y arqueos: mantén tu dinero bajo control.',
                'guia_completa': [
                    {'paso': 1, 'instruccion': 'Al llegar, abre la caja desde el Panel Central clicando en "Apertura de Caja".', 'detalles': 'Introduce el efectivo inicial con el que arrancas la jornada.'},
                    {'paso': 2, 'instruccion': 'Visualiza tu balance real.', 'detalles': 'En el TPV, verás una barra superior (Balance Total) que suma tu fondo inicial + ventas del día.'},
                    {'paso': 3, 'instruccion': 'Realiza arqueos periódicos.', 'detalles': 'En el menú "Caja", selecciona el tipo de arqueo (Diario, Semanal, etc.) para ver el resumen de movimientos.'},
                    {'paso': 4, 'instruccion': 'Cierra la caja al terminar.', 'detalles': 'Registra el efectivo final y compara con el "Esperado" para detectar posibles descuadres.'},
                ],
                'notas_importantes': [
                    'Nunca borres el fondo inicial una vez establecida la apertura.',
                    'Los descuadres de caja se resaltarán en rojo en los informes de arqueo.'
                ]
            },
            {
                'id': 'inventario',
                'titulo': 'Gestión de Inventario',
                'icono': 'fas fa-box',
                'color': '#f59e0b',
                'descripcion': 'Creación de productos y control de stock mínimo.',
                'guia_completa': [
                    {'paso': 1, 'instruccion': 'Ve a "Productos" en el menú principal.', 'detalles': 'Aquí verás el listado completo de tus artículos y su stock actual.'},
                    {'paso': 2, 'instruccion': 'Clica en "+ Nuevo Producto".', 'detalles': 'Completa el nombre, precio (con IVA incluido), IVA aplicable y stock.'},
                    {'paso': 3, 'instruccion': 'Organiza por Categorías.', 'detalles': 'Asigna categorías a tus productos para que aparezcan agrupados y ordenados en el TPV.'},
                    {'paso': 4, 'instruccion': 'Control de movimientos.', 'detalles': 'Usa la sección "Movimientos de Stock" para ver el histórico de entradas y salidas de cada artículo.'},
                ],
                'notas_importantes': [
                    'Recuerda introducir siempre el Precio Final (PVP) con el IVA ya sumado.',
                    'Si un producto llega a stock cero, aparecerá un aviso en el panel de control.'
                ]
            },
        ]
        return context


# ============================================================
# ACERCA DE / VERSION
# ============================================================

class AboutVersionView(LoginRequiredMixin, TemplateView):
    template_name = 'home/acerca_version.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['app_version'] = os.environ.get('KUDEA_VERSION', '1.0.0')
        context['build_id'] = os.environ.get('KUDEA_BUILD', 'local')
        context['runtime_env'] = 'development' if settings.DEBUG else 'production'
        return context


# ============================================================
# COMUNICACIONES INTERNAS
# ============================================================

from django.contrib.auth.decorators import login_required

@login_required
def mark_comms_read(request):
    if request.method == 'POST':
        from applications.home.models import Comunicacion
        comms = Comunicacion.objects.exclude(visto_por=request.user)
        for c in comms:
            c.visto_por.add(request.user)
        return JsonResponse({'ok': True})
    return JsonResponse({'ok': False}, status=400)

@login_required
def create_comm(request):
    if request.method == 'POST' and request.user.is_staff:
        from applications.home.models import Comunicacion
        titulo = request.POST.get('titulo')
        contenido = request.POST.get('contenido')
        if titulo and contenido:
            Comunicacion.objects.create(
                emisor=request.user,
                titulo=titulo,
                contenido=contenido
            )
            return JsonResponse({'ok': True})
    return JsonResponse({'ok': False}, status=400)
