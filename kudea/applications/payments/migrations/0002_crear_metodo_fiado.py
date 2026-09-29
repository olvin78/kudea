from django.db import migrations


def crear_metodo_fiado(apps, schema_editor):
    """Método de pago FIADO: la venta no entra en caja hasta que el cliente paga."""
    MetodoPago = apps.get_model("payments", "MetodoPago")
    MetodoPago.objects.get_or_create(
        nombre="Fiado",
        defaults={"activo": True, "acepta_cambio": False},
    )


def borrar_metodo_fiado(apps, schema_editor):
    MetodoPago = apps.get_model("payments", "MetodoPago")
    MetodoPago.objects.filter(nombre="Fiado").delete()


class Migration(migrations.Migration):

    dependencies = [
        ("payments", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(crear_metodo_fiado, borrar_metodo_fiado),
    ]
