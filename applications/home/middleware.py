# Permite redirigir a otra página
from django.shortcuts import redirect

# Modelo donde guardas si el módulo está activo o no
from applications.home.models import Modulo


class ModuloActivoMiddleware:

    def __init__(self, get_response):
        self.get_response = get_response

        # Relaciona la primera parte de la URL con la clave en la base de datos
        # Ejemplo:
        # /invoices/  → clave "facturas"
        self.segmento_a_clave = {
            "invoices": "facturas",
            "budget": "presupuestos",
            "cash": "caja",
            "stock": "stock",
            "support": "soporte",
            "reporting": "informes",
            "cashflow": "movimientos_caja",
            "payments": "formas_pago",
            "accounts": "cuentas",
            "recordlog": "orden_registros",
            "attendance": "registro_horas",
            "employees": "empleados",
            "tpv_shop": "tpv_shop",
        }

    def __call__(self, request):

        # Obtener la URL que el usuario está visitando
        path = request.path

        # Extraer el primer segmento real de la URL
        # Ejemplo:
        # /invoices/nueva/  → invoices
        segmento = path.lstrip("/").split("/", 1)[0]

        # Ver si esa URL corresponde a un módulo controlado
        clave = self.segmento_a_clave.get(segmento)

        # Si no es un módulo que controlamos, dejamos pasar
        if not clave:
            return self.get_response(request)

        # Buscar en la base de datos si ese módulo está activo
        activo = Modulo.objects.filter(clave=clave, activo=True).exists()

        # Si el módulo está desactivado, redirigir al home
        if not activo:
            return redirect("/")

        # Si está activo, dejar que la petición continúe
        return self.get_response(request)