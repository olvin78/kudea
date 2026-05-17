import os
from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views import View
from decimal import Decimal
from django.db.models import Count

from applications.config.models import ConfiguracionFiscal
from applications.home.models import Modulo, ConfiguracionTPV
from applications.payments.models import MetodoPago
from applications.product.models import Producto, Categoria
from applications.tpv.models import Empleado
from applications.cash.models import AperturaCaja


class ConfiguracionesView(LoginRequiredMixin, View):
    template_name = 'config/configuraciones.html'

    def get(self, request):
        # Obtener o crear configuraciones globales
        config_fiscal = ConfiguracionFiscal.objects.first()
        if not config_fiscal:
            config_fiscal = ConfiguracionFiscal.objects.create(
                nombre="Configuración General", 
                iva_general=21.00, 
                fondo_caja_defecto=200.00
            )

        config_tpv = ConfiguracionTPV.objects.first()
        if not config_tpv:
            config_tpv = ConfiguracionTPV.objects.create(
                nombre_tienda="Kudea Shop", 
                iva_por_defecto=21.00, 
                moneda="€", 
                imprimir_tickets=True, 
                mostrar_stock=True
            )

        modulos = Modulo.objects.all().order_by('nombre')
        metodos_pago = MetodoPago.objects.all().order_by('nombre')
        
        # Obtener empleados y categorías con su conteo de productos
        empleados = Empleado.objects.all().order_by('nombre')
        categorias = Categoria.objects.annotate(total_productos=Count('products')).order_by('nombre')
        
        # Obtener cajas registradoras abiertas en tiempo real
        cajas_activas = AperturaCaja.objects.filter(estado='abierta').order_by('-hora_apertura')
        
        # Conteo total de productos en catálogo
        total_productos = Producto.objects.count()

        context = {
            'config_fiscal': config_fiscal,
            'config_tpv': config_tpv,
            'modulos': modulos,
            'metodos_pago': metodos_pago,
            'empleados': empleados,
            'categorias': categorias,
            'cajas_activas': cajas_activas,
            'total_cajas_activas': cajas_activas.count(),
            'total_productos': total_productos,
        }
        return render(request, self.template_name, context)

    def post(self, request):
        config_fiscal = ConfiguracionFiscal.objects.first()
        config_tpv = ConfiguracionTPV.objects.first()

        # 1. Crear nueva categoría si el formulario fue enviado para ello
        if 'crear_categoria_btn' in request.POST:
            cat_nombre = request.POST.get('categoria_nombre_nuevo', '').strip()
            if cat_nombre:
                if not Categoria.objects.filter(nombre__iexact=cat_nombre).exists():
                    Categoria.objects.create(nombre=cat_nombre)
                    messages.success(request, f"Categoría '{cat_nombre}' añadida al catálogo con éxito.")
                else:
                    messages.warning(request, f"La categoría '{cat_nombre}' ya existe en el sistema.")
            return redirect('configuraciones')

        # 2. Guardar Configuración General & TPV
        if config_tpv:
            config_tpv.nombre_tienda = request.POST.get('nombre_tienda', config_tpv.nombre_tienda)
            config_tpv.moneda = request.POST.get('moneda', config_tpv.moneda)
            config_tpv.imprimir_tickets = 'imprimir_tickets' in request.POST
            config_tpv.mostrar_stock = 'mostrar_stock' in request.POST
            
            # Guardar PIN de apertura de caja
            pin_val = request.POST.get('pin_apertura', '1234').strip()
            if len(pin_val) == 4 and pin_val.isdigit():
                config_tpv.pin_apertura = pin_val
            
            # Sincronizar IVA por defecto de TPV
            iva_val = request.POST.get('iva_general', '21.00')
            try:
                config_tpv.iva_por_defecto = float(iva_val)
            except ValueError:
                pass
            config_tpv.save()

        # 3. Guardar Configuración Fiscal
        if config_fiscal:
            config_fiscal.nombre = request.POST.get('nombre_fiscal', config_fiscal.nombre)
            iva_val = request.POST.get('iva_general', '21.00')
            fondo_val = request.POST.get('fondo_caja_defecto', '200.00')
            try:
                config_fiscal.iva_general = float(iva_val)
                config_fiscal.fondo_caja_defecto = float(fondo_val)
            except ValueError:
                pass
            config_fiscal.save()

        # 4. Guardar Estado de Módulos (ON/OFF)
        modulos = Modulo.objects.all()
        for m in modulos:
            field_name = f'modulo_{m.clave}'
            m.activo = field_name in request.POST
            m.save()

        # 5. Guardar Métodos de Pago
        metodos = MetodoPago.objects.all()
        for mp in metodos:
            mp.activo = f'metodo_activo_{mp.id}' in request.POST
            mp.acepta_cambio = f'metodo_cambio_{mp.id}' in request.POST
            mp.save()

        # 6. Guardar Permisos de Empleados
        empleados = Empleado.objects.all()
        for emp in empleados:
            emp.es_administrador = f'emp_admin_{emp.id}' in request.POST
            emp.puede_realizar_salidas = f'emp_salidas_{emp.id}' in request.POST
            emp.puede_cambiar_subtotales = f'emp_subtotales_{emp.id}' in request.POST
            emp.esta_de_baja = f'emp_baja_{emp.id}' in request.POST
            emp.save()

        # 7. SUPERPODERES: Acciones en lote a toda la base de datos
        acciones_lote = []
        
        # A. Sincronizar el IVA general a todos los productos actuales
        if 'forzar_iva_productos' in request.POST:
            try:
                nuevo_iva_dec = Decimal(request.POST.get('iva_general', '21.00'))
                productos_actualizados = Producto.objects.all().update(porcentaje_iva=nuevo_iva_dec)
                acciones_lote.append(f"Se ha aplicado el {nuevo_iva_dec}% de IVA a {productos_actualizados} productos del catálogo.")
            except Exception as e:
                acciones_lote.append(f"Error al sincronizar el IVA general: {str(e)}")

        # B. Sincronizar stock de reposición mínimo a todos los productos
        if 'forzar_stock_minimo' in request.POST:
            nuevo_stock_min = request.POST.get('stock_minimo_val', '5')
            try:
                stock_min_val = int(nuevo_stock_min)
                productos_stock_actualizados = Producto.objects.all().update(stock_minimo=stock_min_val)
                acciones_lote.append(f"Se ha establecido el stock mínimo de reposición a {stock_min_val} unidades para {productos_stock_actualizados} productos.")
            except ValueError:
                pass

        if acciones_lote:
            mensaje_completo = "Configuraciones globales actualizadas con éxito. Acciones en lote: " + " | ".join(acciones_lote)
            messages.success(request, mensaje_completo)
        else:
            messages.success(request, "Configuraciones globales actualizadas con éxito.")

        return redirect('configuraciones')
