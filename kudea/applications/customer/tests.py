import json
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import Client, TestCase

from applications.cashflow.models import Movimiento
from applications.customer.models import Cliente, PagoFiado
from applications.home.models import Venta
from applications.payments.models import MetodoPago
from applications.product.models import Producto


class FiadoTests(TestCase):
    """Fiado = vender sin cobrar: el dinero entra en caja al pagarlo, no antes."""

    def setUp(self):
        self.client = Client()
        self.user = get_user_model().objects.create_user(
            username="cajero", password="secret123"
        )
        self.client.force_login(self.user)

        self.producto = Producto.objects.create(
            nombre="Pan de fiado",
            precio=Decimal("1.50"),
            porcentaje_iva=Decimal("21.00"),
            stock=10,
            stock_minimo=1,
            costo=Decimal("0.60"),
        )
        self.fiado = MetodoPago.objects.get(nombre__iexact="Fiado")
        self.efectivo, _ = MetodoPago.objects.get_or_create(
            nombre="Efectivo", defaults={"activo": True, "acepta_cambio": True}
        )
        self.cliente = Cliente.objects.create(
            nombre="María López", telefono="8888-8888"
        )

    def _vender(self, **extra):
        payload = {
            "ticket": [{"id": self.producto.id, "cantidad": 2, "precio": "1.50"}],
            "metodo_pago": self.fiado.id,
            "recibido": 0,
            "descuento": "0.00",
            "cliente_id": self.cliente.id,
        }
        payload.update(extra)
        return self.client.post(
            "/home/api/guardar-venta/",
            data=json.dumps(payload),
            content_type="application/json",
        )

    def test_fiado_requiere_cliente(self):
        response = self._vender(cliente_id=None)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["code"], "CLIENTE_REQUERIDO")

    def test_venta_fiado_no_entra_en_caja(self):
        response = self._vender()
        self.assertEqual(response.status_code, 200, response.content)
        self.assertTrue(response.json()["fiado"])

        venta = Venta.objects.get(id=response.json()["venta_id"])
        self.producto.refresh_from_db()

        # La venta existe, el stock baja… pero NO hay dinero en caja
        self.assertEqual(venta.cliente, self.cliente)
        self.assertEqual(self.producto.stock, 8)
        self.assertEqual(venta.pendiente_fiado, Decimal("3.00"))
        self.assertFalse(
            Movimiento.objects.filter(external_ref=f"tpv:venta:{venta.id}").exists()
        )

        # La pantalla de fiados muestra a la deudora
        page = self.client.get("/fiado/")
        self.assertEqual(page.status_code, 200)
        self.assertContains(page, "María López")

    def test_cobro_parcial_y_total_del_fiado(self):
        response = self._vender()
        venta = Venta.objects.get(id=response.json()["venta_id"])

        # Cobro parcial de 1.00 € → queda 2.00 €
        r2 = self.client.post(
            f"/fiado/cobrar/{venta.id}/",
            {"cantidad": "1.00", "metodo_pago": self.efectivo.id},
        )
        self.assertEqual(r2.status_code, 302)
        venta.refresh_from_db()
        self.assertEqual(venta.pendiente_fiado, Decimal("2.00"))
        self.assertEqual(PagoFiado.objects.count(), 1)

        # Ese cobro SÍ entra en caja (antes no estaba el dinero)
        self.assertTrue(
            Movimiento.objects.filter(
                external_ref="fiado:pago:1", tipo=Movimiento.Tipo.INGRESO
            ).exists()
        )

        # No se puede cobrar de más
        r_error = self.client.post(
            f"/fiado/cobrar/{venta.id}/",
            {"cantidad": "5.00", "metodo_pago": self.efectivo.id},
        )
        self.assertEqual(r_error.status_code, 302)
        venta.refresh_from_db()
        self.assertEqual(venta.pendiente_fiado, Decimal("2.00"))

        # Cobro del resto → cuenta liquidada
        self.client.post(
            f"/fiado/cobrar/{venta.id}/",
            {"cantidad": "2.00", "metodo_pago": self.efectivo.id},
        )
        venta.refresh_from_db()
        self.assertEqual(venta.pendiente_fiado, Decimal("0.00"))

        # El recibo se puede ver
        recibo = self.client.get(
            f"/fiado/recibo/{PagoFiado.objects.latest('id').id}/"
        )
        self.assertEqual(recibo.status_code, 200)
        self.assertContains(recibo, "Pago recibido")

    def test_alta_rapida_de_cliente(self):
        response = self.client.post(
            "/clientes/nuevo-ajax/",
            {"nombre": "Juan Pérez", "telefono": "7777-7777"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()["ok"])
        self.assertTrue(Cliente.objects.filter(nombre="Juan Pérez").exists())

    def test_formulario_propio_de_alta_en_fiado(self):
        """Formulario INDEPENDIENTE del de tpv_shop (no se mezclan)."""
        page = self.client.get("/fiado/cliente/nuevo/")
        self.assertEqual(page.status_code, 200)
        self.assertContains(page, "Nuevo cliente")

        # Sin nombre no se crea
        bad = self.client.post("/fiado/cliente/nuevo/", {"nombre": ""})
        self.assertEqual(bad.status_code, 200)
        self.assertFalse(Cliente.objects.filter(nombre="").exists())

        # Con nombre se crea y vuelve a la pantalla del fiado
        ok = self.client.post(
            "/fiado/cliente/nuevo/",
            {"nombre": "Ana Torres", "telefono": "6666-6666"},
        )
        self.assertEqual(ok.status_code, 302)
        self.assertEqual(ok["Location"], "/fiado/")
        self.assertTrue(Cliente.objects.filter(nombre="Ana Torres").exists())

        # El cliente nuevo sale en la lista de deudores/alta
        self.assertContains(self.client.get("/fiado/"), "Nuevo cliente")
