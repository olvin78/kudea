from django.db import migrations, models


def set_cordoba_currency(apps, schema_editor):
    ConfiguracionTPV = apps.get_model('home', 'ConfiguracionTPV')
    ConfiguracionTPV.objects.filter(moneda__in=['', '€', 'ARS']).update(moneda='C$')


class Migration(migrations.Migration):

    dependencies = [
        ('home', '0007_alter_configuraciontpv_iva_por_defecto'),
    ]

    operations = [
        migrations.AlterField(
            model_name='configuraciontpv',
            name='moneda',
            field=models.CharField(default='C$', max_length=10),
        ),
        migrations.RunPython(set_cordoba_currency, migrations.RunPython.noop),
    ]
