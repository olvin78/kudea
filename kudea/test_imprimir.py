import os
import django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "kudea.settings.local")
django.setup()

from django.test import RequestFactory
from applications.home.models import Venta
from applications.home.views import imprimir_ticket_pos

v = Venta.objects.last()
factory = RequestFactory()
request = factory.post(f"/home/imprimir/{v.id}/")

from django.contrib.auth.models import User
request.user = User.objects.filter(is_superuser=True).first()
response = imprimir_ticket_pos(request, v.id)
print("RESPONSE STATUS:", response.status_code)
if response.status_code != 200:
    print("CONTENT:", response.content.decode())
