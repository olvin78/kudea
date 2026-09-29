# ============================================================
# TESTS DEL MÓDULO DE COMPRAS (app: purchases)
#   1) Proveedor: relación y representación
#   2) Compra: número automático y estado inicial
#   3) Totales: base + IVA = total (por línea y cabecera)
# ============================================================
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase

from applications.product.models import Producto

from .models import Compra, CompraItem, Proveedor


class ComprasModelsTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="compras_test", password="secret123"
        )
        self.proveedor = Proveedor.objects.create(
            nombre="Distribuidora Norte",
            nit="J05010012345678",
            telefono="2222-3333",
        )
        self.producto = Producto.objects.create(
            nombre="Agua mineral 5L",
            precio=Decimal("30.00"),
            porcentaje_iva=Decimal("15.00"),
            costo=Decimal("20.00"),
            stock=0,
            stock_minimo=2,
        )

    def test_proveedor_relacion_y_str(self):
        self.assertEqual(str(self.proveedor), "Distribuidora Norte")
        self.assertEqual(self.proveedor.compras_count, 0)

    def test_numero_compra_automatico(self):
        compra1 = Compra.objects.create(proveedor=self.proveedor, creada_por=self.user)
        compra2 = Compra.objects.create(proveedor=self.proveedor, creada_por=self.user)
        self.assertEqual(compra1.numero, "COM-000001")
        self.assertEqual(compra2.numero, "COM-000002")

    def test_estado_inicial_borrador(self):
        compra = Compra.objects.create(proveedor=self.proveedor, creada_por=self.user)
        self.assertEqual(compra.estado, "borrador")
        self.assertFalse(compra.recibida)

    def test_totales_base_mas_iva_por_lineas(self):
        compra = Compra.objects.create(proveedor=self.proveedor, creada_por=self.user)
        # 3 x 20,00 con IVA 15%  -> base 60,00 iva 9,00
        CompraItem.objects.create(
            compra=compra, producto=self.producto, cantidad=3,
            precio_unitario=Decimal("20.00"), porcentaje_iva=Decimal("15.00"),
        )
        # 1 x 10,00 exento        -> base 10,00 iva 0,00
        CompraItem.objects.create(
            compra=compra, producto=self.producto, cantidad=1,
            precio_unitario=Decimal("10.00"), porcentaje_iva=Decimal("0.00"),
        )

        compra.refresh_from_db()
        self.assertEqual(compra.subtotal, Decimal("70.00"))
        self.assertEqual(compra.iva, Decimal("9.00"))
        self.assertEqual(compra.total, Decimal("79.00"))
        # Invariante del módulo: base + cuota = total
        self.assertEqual(compra.subtotal + compra.iva, compra.total)

    def test_linea_hereda_iva_del_producto(self):
        compra = Compra.objects.create(proveedor=self.proveedor, creada_por=self.user)
        item = CompraItem.objects.create(
            compra=compra, producto=self.producto, cantidad=2,
            precio_unitario=Decimal("15.00"),
        )
        self.assertEqual(item.porcentaje_iva, Decimal("15.00"))
        self.assertEqual(item.subtotal, Decimal("30.00"))
        self.assertEqual(item.iva_importe, Decimal("4.50"))
        self.assertEqual(item.total, Decimal("34.50"))


# ============================================================
# TESTS DE VISTAS (paso 2): rutas, login y CRUD de proveedores
# ============================================================
from django.test import Client
from django.urls import reverse


class ComprasViewsTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="compras_views", password="secret123"
        )
        self.proveedor = Proveedor.objects.create(nombre="Snacks La Bendición")

    def test_rutas_exigen_login(self):
        """Las 3 páginas del módulo redirigen al login si no hay sesión."""
        for url in (
            reverse("purchases_app:compra_list"),
            reverse("purchases_app:proveedor_list"),
            reverse("purchases_app:proveedor_create"),
        ):
            response = self.client.get(url)
            self.assertEqual(response.status_code, 302, url)

    def test_lista_compras_muestra_la_compra(self):
        compra = Compra.objects.create(proveedor=self.proveedor, creada_por=self.user)
        self.client.force_login(self.user)
        response = self.client.get(reverse("purchases_app:compra_list"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, compra.numero)
        self.assertContains(response, self.proveedor.nombre)

    def test_lista_compras_filtra_por_estado(self):
        Compra.objects.create(proveedor=self.proveedor, creada_por=self.user)
        self.client.force_login(self.user)
        response = self.client.get(reverse("purchases_app:compra_list"), {"estado": "recibida"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context["compras"]), 0)

    def test_lista_proveedores_muestra_proveedor(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse("purchases_app:proveedor_list"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Snacks La Bendición")

    def test_alta_de_proveedor(self):
        self.client.force_login(self.user)
        response = self.client.post(
            reverse("purchases_app:proveedor_create"),
            {
                "nombre": "Bebidas del Sur",
                "nit": "J0011223344",
                "contacto": "María",
                "telefono": "8888-1111",
                "email": "ventas@sur.test",
                "direccion": "Mercado Oriental",
                "dias_entrega": "martes",
                "activo": "on",
                "notas": "",
            },
        )
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Proveedor.objects.filter(nombre="Bebidas del Sur").exists())

    def test_edicion_de_proveedor(self):
        self.client.force_login(self.user)
        url = reverse("purchases_app:proveedor_update", args=[self.proveedor.pk])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Snacks La Bendición")

        response = self.client.post(
            url,
            {
                "nombre": "Snacks La Bendición S.A.",
                "nit": "",
                "contacto": "",
                "telefono": "",
                "email": "",
                "direccion": "",
                "dias_entrega": "",
                "activo": "on",
                "notas": "",
            },
        )
        self.assertEqual(response.status_code, 302)
        self.proveedor.refresh_from_db()
        self.assertEqual(self.proveedor.nombre, "Snacks La Bendición S.A.")


# ============================================================
# TESTS DEL FLUJO (paso 3): crear compra -> recibir -> stock
# ============================================================
from applications.stock.models import Movement


class CompraFlujoTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="compras_flujo", password="secret123"
        )
        self.client.force_login(self.user)
        self.proveedor = Proveedor.objects.create(nombre="Distribuidora Central")
        self.producto = Producto.objects.create(
            nombre="Arroz 1kg", precio=Decimal("35.00"),
            porcentaje_iva=Decimal("15.00"), costo=Decimal("18.00"),
            stock=0, stock_minimo=2,
        )

    def _lineas(self, cantidad="10", precio="20.00", iva="15"):
        """Datos del formset de líneas (una línea real y una vacía)."""
        return {
            "items-TOTAL_FORMS": "2", "items-INITIAL_FORMS": "0",
            "items-MIN_NUM_FORMS": "0", "items-MAX_NUM_FORMS": "1000",
            "items-0-producto": str(self.producto.pk),
            "items-0-cantidad": cantidad,
            "items-0-precio_unitario": precio,
            "items-0-porcentaje_iva": iva,
            "items-1-producto": "", "items-1-cantidad": "",
            "items-1-precio_unitario": "", "items-1-porcentaje_iva": "",
        }

    def _post_nueva(self, extra=None):
        data = {
            "proveedor": str(self.proveedor.pk),
            "fecha": "2026-09-27",
            "notas": "Pedido semanal",
        }
        data.update(self._lineas())
        data.update(extra or {})
        return self.client.post(reverse("purchases_app:compra_create"), data)

    def _compra_linea(self, cantidad=10, precio=Decimal("20.00")):
        compra = Compra.objects.create(proveedor=self.proveedor, creada_por=self.user)
        CompraItem.objects.create(
            compra=compra, producto=self.producto, cantidad=cantidad,
            precio_unitario=precio, porcentaje_iva=Decimal("15.00"),
        )
        return compra

    # ---- CREAR ----
    def test_crear_compra_con_lineas(self):
        response = self._post_nueva()
        self.assertEqual(response.status_code, 302)

        compra = Compra.objects.get()
        self.assertEqual(compra.estado, "borrador")
        self.assertEqual(compra.creada_por, self.user)
        self.assertEqual(compra.items.count(), 1)
        # base 10 x 20 = 200 · IVA 15% = 30 · total 230
        self.assertEqual(compra.subtotal, Decimal("200.00"))
        self.assertEqual(compra.iva, Decimal("30.00"))
        self.assertEqual(compra.total, Decimal("230.00"))
        # el stock NO se toca hasta recibir
        self.producto.refresh_from_db()
        self.assertEqual(self.producto.stock, 0)
        self.assertEqual(self.producto.costo, Decimal("18.00"))

    def test_crear_compra_sin_lineas_no_se_guarda(self):
        vacias = {
            "items-0-producto": "", "items-0-cantidad": "",
            "items-0-precio_unitario": "", "items-0-porcentaje_iva": "",
        }
        response = self._post_nueva(extra=vacias)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Compra.objects.count(), 0)
        self.assertContains(response, "al menos un producto")

    # ---- RECIBIR ----
    def test_recibir_sube_stock_coste_y_movimiento(self):
        compra = self._compra_linea(cantidad=7, precio=Decimal("21.50"))
        response = self.client.post(
            reverse("purchases_app:compra_recibir", args=[compra.pk])
        )
        self.assertEqual(response.status_code, 302)

        self.producto.refresh_from_db()
        self.assertEqual(self.producto.stock, 7)              # stock subido
        self.assertEqual(self.producto.costo, Decimal("21.50"))  # coste actualizado

        compra.refresh_from_db()
        self.assertEqual(compra.estado, "recibida")
        self.assertIsNotNone(compra.recibida_en)

        movimiento = Movement.objects.get()
        self.assertEqual(movimiento.tipo, "entrada")
        self.assertEqual(movimiento.cantidad, 7)
        self.assertIn(compra.numero, movimiento.observaciones)

    def test_recibir_dos_veces_no_duplica_stock(self):
        compra = self._compra_linea(cantidad=7)
        for _ in range(2):
            self.client.post(reverse("purchases_app:compra_recibir", args=[compra.pk]))
        self.producto.refresh_from_db()
        self.assertEqual(self.producto.stock, 7)
        self.assertEqual(Movement.objects.count(), 1)

    # ---- CANCELAR ----
    def test_cancelar_no_toca_stock(self):
        compra = self._compra_linea(cantidad=5)
        response = self.client.post(
            reverse("purchases_app:compra_cancelar", args=[compra.pk])
        )
        self.assertEqual(response.status_code, 302)
        compra.refresh_from_db()
        self.assertEqual(compra.estado, "cancelada")
        self.producto.refresh_from_db()
        self.assertEqual(self.producto.stock, 0)
        self.assertEqual(Movement.objects.count(), 0)

        # Una compra cancelada ya no se puede recibir
        self.client.post(reverse("purchases_app:compra_recibir", args=[compra.pk]))
        self.producto.refresh_from_db()
        self.assertEqual(self.producto.stock, 0)
        self.assertEqual(Movement.objects.count(), 0)
