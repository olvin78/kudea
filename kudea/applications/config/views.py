import os
import random
from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views import View
from decimal import Decimal, InvalidOperation
from django.db.models import Count

from applications.config.models import ConfiguracionFiscal
from applications.home.models import Modulo, ConfiguracionTPV
from applications.payments.models import MetodoPago
from applications.product.models import Producto, Categoria
from applications.tpv.models import Empleado
from applications.cash.models import AperturaCaja, Caja


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
                moneda="C$", 
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
        cajas = Caja.objects.all().order_by('nombre')
        
        # Anotar cada caja con su usuario activo
        for c in cajas:
            c.usuario_activo = None
        for ap in cajas_activas:
            if ap.caja_id:
                for c in cajas:
                    if c.id == ap.caja_id:
                        c.usuario_activo = ap.usuario
                        break
        
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
            'cajas': cajas,
            'cajas_abiertas_usuario': cajas_activas,
            'total_productos': total_productos,
        }
        return render(request, self.template_name, context)

    def post(self, request):
        config_fiscal = ConfiguracionFiscal.objects.first()
        config_tpv = ConfiguracionTPV.objects.first()

        # 0. Crear nueva caja
        if 'crear_caja_btn' in request.POST:
            caja_nombre = request.POST.get('caja_nombre_nuevo', '').strip()
            caja_pin = request.POST.get('caja_pin_nuevo', '1234').strip()
            if caja_nombre:
                if not Caja.objects.filter(nombre__iexact=caja_nombre).exists():
                    Caja.objects.create(nombre=caja_nombre, pin=caja_pin[:4] if caja_pin else '1234')
                    messages.success(request, f"Caja '{caja_nombre}' creada con éxito.")
                else:
                    messages.warning(request, f"Ya existe una caja llamada '{caja_nombre}'.")
            return redirect('configuraciones')

        # 0b. Eliminar caja
        if 'eliminar_caja_btn' in request.POST:
            caja_id = request.POST.get('eliminar_caja_id', '')
            caja = Caja.objects.filter(id=caja_id).first()
            if caja:
                if caja.predeterminada:
                    messages.error(request, f"'{caja.nombre}' es la caja predeterminada y no se puede eliminar.")
                elif AperturaCaja.objects.filter(caja=caja, estado='abierta').exists():
                    messages.error(request, f"No se puede eliminar '{caja.nombre}' porque tiene aperturas activas.")
                else:
                    caja.delete()
                    messages.success(request, f"Caja '{caja.nombre}' eliminada.")
            return redirect('configuraciones')

        # 1. Crear nueva categoría si el formulario fue enviado para ello
        if 'crear_categoria_btn' in request.POST:
            cat_nombre = request.POST.get('categoria_nombre_nuevo', '').strip()
            cat_desc = request.POST.get('categoria_descripcion_nueva', '').strip()
            if cat_nombre:
                if not Categoria.objects.filter(nombre__iexact=cat_nombre).exists():
                    Categoria.objects.create(nombre=cat_nombre, descripcion=cat_desc or None)
                    messages.success(request, f"Categoría '{cat_nombre}' añadida al catálogo con éxito.")
                else:
                    messages.warning(request, f"La categoría '{cat_nombre}' ya existe en el sistema.")
            return redirect('configuraciones')

        # ── Valores previos: para poder decir en la notificación QUÉ cambió ──
        def _vals(obj, *campos):
            return tuple(getattr(obj, c, None) for c in campos) if obj else None

        _campos_tpv = ('nombre_tienda', 'moneda', 'imprimir_tickets', 'mostrar_stock', 'pin_apertura', 'iva_por_defecto')
        _campos_fiscal = ('iva_general', 'fondo_caja_defecto')
        prev = {
            'tpv': _vals(config_tpv, *_campos_tpv),
            'fiscal': _vals(config_fiscal, *_campos_fiscal),
            'modulos': {m.id: m.activo for m in Modulo.objects.all()},
            'metodos': {m.id: (m.activo, m.acepta_cambio) for m in MetodoPago.objects.all()},
            'categorias': {c.id: c.porcentaje_iva for c in Categoria.objects.all()},
            'empleados': {e.id: (e.es_administrador, e.puede_realizar_salidas, e.puede_cambiar_subtotales, e.esta_de_baja) for e in Empleado.objects.all()},
        }

        # 2. Guardar Configuración General & TPV
        if config_tpv:
            config_tpv.nombre_tienda = request.POST.get('nombre_tienda', config_tpv.nombre_tienda)
            config_tpv.moneda = request.POST.get('moneda', config_tpv.moneda)
            config_tpv.imprimir_tickets = 'imprimir_tickets' in request.POST
            config_tpv.mostrar_stock = 'mostrar_stock' in request.POST
            
            # Guardar PIN de apertura de caja (protegido con contraseña)
            pin_val = request.POST.get('pin_apertura', '1234').strip()
            pin_actual = str(config_tpv.pin_apertura).strip() if config_tpv.pin_apertura else '1234'
            if pin_val != pin_actual and len(pin_val) == 4 and pin_val.isdigit():
                password_confirm = request.POST.get('pin_password_confirm', '')
                if password_confirm and request.user.check_password(password_confirm):
                    config_tpv.pin_apertura = pin_val
                elif password_confirm:
                    messages.error(request, "Contraseña incorrecta. El PIN de apertura no se modificó.")
                else:
                    messages.warning(request, "Debes ingresar tu contraseña para cambiar el PIN de apertura.")
            elif len(pin_val) == 4 and pin_val.isdigit():
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

        # 6. SUPERPODERES: Acciones en lote a toda la base de datos
        acciones_lote = []

        # 7. Guardar IVA por categoría + sync productos
        categorias = Categoria.objects.all()
        for cat in categorias:
            iva_cat_key = f'categoria_iva_{cat.id}'
            if iva_cat_key in request.POST:
                try:
                    iva_cat_val = Decimal(request.POST.get(iva_cat_key))
                    cat.porcentaje_iva = iva_cat_val
                    cat.save()
                except (ValueError, TypeError, InvalidOperation):
                    pass

            # Sync productos de esta categoría al IVA de la categoría
            if f'categoria_sync_{cat.id}' in request.POST and cat.porcentaje_iva is not None:
                actualizados = Producto.objects.filter(categoria=cat).update(porcentaje_iva=cat.porcentaje_iva)
                if actualizados:
                    acciones_lote.append(f"Categoría '{cat.nombre}': IVA {cat.porcentaje_iva}% aplicado a {actualizados} productos.")

        # 8. Guardar Permisos de Empleados
        empleados = Empleado.objects.all()
        for emp in empleados:
            emp.es_administrador = f'emp_admin_{emp.id}' in request.POST
            emp.puede_realizar_salidas = f'emp_salidas_{emp.id}' in request.POST
            emp.puede_cambiar_subtotales = f'emp_subtotales_{emp.id}' in request.POST
            emp.esta_de_baja = f'emp_baja_{emp.id}' in request.POST
            emp.save()

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

        # ── Resumen de lo que REALMENTE ha cambiado ──
        if config_tpv:
            config_tpv.refresh_from_db()
        if config_fiscal:
            config_fiscal.refresh_from_db()

        cambios = []

        def _fmt(v):
            if isinstance(v, bool):
                return 'ON' if v else 'OFF'
            return str(v)

        if config_tpv and prev['tpv']:
            etiquetas = ['Nombre de tienda', 'Moneda', 'Auto-imprimir tickets', 'Mostrar stock', 'PIN de apertura', 'IVA por defecto']
            for etiqueta, antes, ahora in zip(etiquetas, prev['tpv'], _vals(config_tpv, *_campos_tpv)):
                if antes != ahora:
                    cambios.append(f"{etiqueta}: {_fmt(antes)} → {_fmt(ahora)}")

        if config_fiscal and prev['fiscal']:
            etiquetas = ['IVA general', 'Fondo de caja por defecto']
            for etiqueta, antes, ahora in zip(etiquetas, prev['fiscal'], _vals(config_fiscal, *_campos_fiscal)):
                if antes != ahora:
                    cambios.append(f"{etiqueta}: {_fmt(antes)} → {_fmt(ahora)}")

        for m in Modulo.objects.all():
            antes = prev['modulos'].get(m.id)
            if antes is not None and antes != m.activo:
                cambios.append(f"Módulo '{m.nombre}': {_fmt(m.activo)}")

        for mp in MetodoPago.objects.all():
            antes = prev['metodos'].get(mp.id)
            if antes is not None and antes != (mp.activo, mp.acepta_cambio):
                estado = _fmt(mp.activo) + (', admite cambio' if mp.acepta_cambio else '')
                cambios.append(f"Método '{mp.nombre}': {estado}")

        for cat in Categoria.objects.all():
            antes = prev['categorias'].get(cat.id)
            if antes is not None and antes != cat.porcentaje_iva:
                cambios.append(f"IVA de '{cat.nombre}': {antes}% → {cat.porcentaje_iva}%")

        for emp in Empleado.objects.all():
            antes = prev['empleados'].get(emp.id)
            if antes is not None and antes != (emp.es_administrador, emp.puede_realizar_salidas, emp.puede_cambiar_subtotales, emp.esta_de_baja):
                permisos = [n for n, v in zip(
                    ('administrador', 'salidas', 'subtotales'),
                    (emp.es_administrador, emp.puede_realizar_salidas, emp.puede_cambiar_subtotales),
                ) if v]
                cambios.append(f"Permisos de {emp.nombre}: {', '.join(permisos) if permisos else 'ninguno'}")

        if cambios:
            resumen = "Guardado → " + "; ".join(cambios)
        else:
            resumen = "Ajustes guardados (ningún valor cambió)."

        if acciones_lote:
            resumen += " · Lote: " + " | ".join(acciones_lote)

        messages.success(request, resumen)

        return redirect('configuraciones')


class RefreshPinView(LoginRequiredMixin, View):
    def post(self, request, caja_id):
        caja = Caja.objects.filter(id=caja_id).first()
        if not caja:
            return redirect('configuraciones')
        nuevo_pin = f"{random.randint(0, 9999):04d}"
        caja.pin = nuevo_pin
        caja.save()
        messages.success(request, f"PIN de '{caja.nombre}' actualizado a {nuevo_pin}")
        return redirect('configuraciones')
