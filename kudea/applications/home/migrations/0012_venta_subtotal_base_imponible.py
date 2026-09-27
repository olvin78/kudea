from decimal import Decimal

from django.db import migrations


def subtotal_es_base_imponible(apps, schema_editor):
    """Las ventas antiguas guardaban en `subtotal` la suma con IVA incluido.

    Se recalcula como base imponible real para que siempre se cumpla:
    subtotal (base) + iva (cuota) = total.
    """
    Venta = apps.get_model("home", "Venta")
    for venta in Venta.objects.all().iterator():
        iva = venta.iva or Decimal("0")
        total = venta.total or Decimal("0")
        base = total - iva
        if venta.subtotal != base:
            venta.subtotal = base
            venta.save(update_fields=["subtotal"])


class Migration(migrations.Migration):

    dependencies = [
        ("home", "0011_alter_configuraciontpv_moneda"),
    ]

    operations = [
        migrations.RunPython(subtotal_es_base_imponible, migrations.RunPython.noop),
    ]
