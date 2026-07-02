import os
import django
import json

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "kudea.settings")
django.setup()

from django.test import RequestFactory
from applications.home.views import guardar_venta
from django.contrib.auth.models import User

user = User.objects.filter(is_superuser=True).first()
factory = RequestFactory()
from applications.home.models import Producto
producto = Producto.objects.first()
data = {
    "ticket": [{"id": producto.id, "cantidad": 1, "precio": float(producto.precio), "iva": 21, "nombre": "Test"}],
    "metodo_pago": 1,
    "recibido": float(producto.precio),
    "descuento": 0
}
request = factory.post('/home/guardar_venta/', data=json.dumps(data), content_type='application/json')
setattr(request, '_dont_enforce_csrf_checks', True)
request.user = user

try:
    response = guardar_venta(request)
    print("Status:", response.status_code)
    print("Content:", response.content.decode('utf-8'))
except Exception as e:
    import traceback
    traceback.print_exc()
