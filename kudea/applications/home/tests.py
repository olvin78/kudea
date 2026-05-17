import json
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import Client, TestCase

from applications.cash.models import AperturaCaja, CierreCaja
from applications.cashflow.models import Movimiento
from applications.config.models import ConfiguracionFiscal
from applications.home.models import DetalleVenta, Venta
from applications.payments.models import MetodoPago
from applications.product.models import Producto


class HomeSalesFlowTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = get_user_model().objects.create_user(
            username="tester",
            email="tester@example.com",
            password="secret123",
        )
        self.client.force_login(self.user)

        ConfiguracionFiscal.objects.create(
            nombre="Configuracion Test",
            iva_general=Decimal("21.00"),
            fondo_caja_defecto=Decimal("200.00"),
        )

        self.cash_method = MetodoPago.objects.create(
            nombre="Cash",
            activo=True,
            acepta_cambio=True,
        )
        self.card_method = MetodoPago.objects.create(
            nombre="Card",
            activo=True,
            acepta_cambio=False,
        )

    def test_crear_producto_desde_formulario(self):
        response = self.client.post(
            "/home/productos/crear/",
            {
                "codigo_barras": "",
                "nombre": "Producto Test",
                "categoria": "",
                "precio": "10.00",
                "porcentaje_iva": "21.00",
                "descuento": "0",
                "costo": "5.00",
                "stock": "7",
                "stock_minimo": "2",
                "tipo_producto": "fisico",
                "activo": "on",
            },
        )

        self.assertEqual(response.status_code, 302)

        producto = Producto.objects.get(nombre="Producto Test")
        self.assertEqual(producto.stock, 7)
        self.assertTrue(producto.codigo_barras.startswith("KUD-"))

    def test_guardar_venta_actualiza_stock_historial_y_cashflow(self):
        AperturaCaja.objects.create(
            usuario=self.user,
            fondo_inicial=Decimal("100.00"),
            estado="abierta",
        )
        producto_a = Producto.objects.create(
            nombre="Producto A",
            precio=Decimal("10.00"),
            porcentaje_iva=Decimal("21.00"),
            stock=5,
            stock_minimo=1,
        )
        producto_b = Producto.objects.create(
            nombre="Producto B",
            precio=Decimal("20.00"),
            porcentaje_iva=Decimal("10.00"),
            stock=8,
            stock_minimo=2,
        )

        response = self.client.post(
            "/home/api/guardar-venta/",
            data=json.dumps(
                {
                    "ticket": [
                        {"id": producto_a.id, "cantidad": 1, "precio": "10.00"},
                        {"id": producto_b.id, "cantidad": 2, "precio": "20.00"},
                    ],
                    "metodo_pago": self.cash_method.id,
                    "recibido": "70.00",
                    "descuento": "0.00",
                }
            ),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertTrue(payload["success"])

        venta = Venta.objects.get(id=payload["venta_id"])
        producto_a.refresh_from_db()
        producto_b.refresh_from_db()

        self.assertEqual(venta.total, Decimal("56.10"))
        self.assertEqual(producto_a.stock, 4)
        self.assertEqual(producto_b.stock, 6)
        self.assertEqual(DetalleVenta.objects.filter(venta=venta).count(), 2)

        historial = self.client.get("/home/ventas/")
        self.assertContains(historial, venta.codigo)

        detalle = self.client.get(f"/home/venta/{venta.id}/")
        self.assertContains(detalle, "Producto A")
        self.assertContains(detalle, "Producto B")

        movimiento = Movimiento.objects.get(external_ref=f"tpv:venta:{venta.id}")
        self.assertEqual(movimiento.cuenta.nombre, "Caja")
        self.assertEqual(movimiento.metodo_pago, Movimiento.MetodoPago.EFECTIVO)

    def test_guardar_venta_rechaza_stock_insuficiente(self):
        producto = Producto.objects.create(
            nombre="Producto Sin Stock",
            precio=Decimal("15.00"),
            porcentaje_iva=Decimal("21.00"),
            stock=2,
            stock_minimo=1,
        )

        response = self.client.post(
            "/home/api/guardar-venta/",
            data=json.dumps(
                {
                    "ticket": [
                        {"id": producto.id, "cantidad": 3, "precio": "15.00"},
                    ],
                    "metodo_pago": self.card_method.id,
                    "recibido": "0.00",
                    "descuento": "0.00",
                }
            ),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 400)
        self.assertFalse(response.json()["success"])

        producto.refresh_from_db()
        self.assertEqual(producto.stock, 2)
        self.assertEqual(Venta.objects.count(), 0)

    def test_cierre_diario_guarda_totales_y_cierra_apertura(self):
        AperturaCaja.objects.create(
            usuario=self.user,
            fondo_inicial=Decimal("100.00"),
            estado="abierta",
        )
        producto = Producto.objects.create(
            nombre="Producto Cierre",
            precio=Decimal("10.00"),
            porcentaje_iva=Decimal("21.00"),
            stock=5,
            stock_minimo=1,
        )

        sale_response = self.client.post(
            "/home/api/guardar-venta/",
            data=json.dumps(
                {
                    "ticket": [
                        {"id": producto.id, "cantidad": 1, "precio": "10.00"},
                    ],
                    "metodo_pago": self.cash_method.id,
                    "recibido": "20.00",
                    "descuento": "0.00",
                }
            ),
            content_type="application/json",
        )
        self.assertEqual(sale_response.status_code, 200)

        response = self.client.post("/home/arqueo/diario/", follow=True)
        self.assertEqual(response.status_code, 200)

        cierre = CierreCaja.objects.get(tipo="diario")
        apertura = AperturaCaja.objects.get(usuario=self.user)

        self.assertEqual(cierre.total_ventas, Decimal("12.10"))
        self.assertEqual(cierre.efectivo_esperado, Decimal("112.10"))
        self.assertEqual(cierre.efectivo_retirado, Decimal("12.10"))
        self.assertEqual(apertura.estado, "cerrada")
