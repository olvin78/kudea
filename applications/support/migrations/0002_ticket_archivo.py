# Generated by Django 5.2 on 2025-04-03 20:55

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('support', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='ticket',
            name='archivo',
            field=models.FileField(blank=True, null=True, upload_to='tickets/archivos/'),
        ),
    ]
