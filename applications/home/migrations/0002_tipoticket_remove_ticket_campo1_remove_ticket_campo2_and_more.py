# Generated by Django 5.2 on 2025-04-03 19:29

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('home', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='TipoTicket',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nombre', models.CharField(blank=True, max_length=100, null=True, unique=True)),
            ],
        ),
        migrations.RemoveField(
            model_name='ticket',
            name='campo1',
        ),
        migrations.RemoveField(
            model_name='ticket',
            name='campo2',
        ),
        migrations.RemoveField(
            model_name='ticket',
            name='campo3',
        ),
        migrations.AddField(
            model_name='ticket',
            name='actualizado',
            field=models.DateTimeField(auto_now=True, null=True),
        ),
        migrations.AddField(
            model_name='ticket',
            name='asunto',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AddField(
            model_name='ticket',
            name='cliente',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='tickets', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='ticket',
            name='creado',
            field=models.DateTimeField(auto_now_add=True, null=True),
        ),
        migrations.AddField(
            model_name='ticket',
            name='estado',
            field=models.CharField(choices=[('abierto', 'Abierto'), ('en_progreso', 'En progreso'), ('cerrado', 'Cerrado')], default='abierto', max_length=20),
        ),
        migrations.AddField(
            model_name='ticket',
            name='identificador',
            field=models.CharField(blank=True, editable=False, max_length=10, null=True, unique=True),
        ),
        migrations.AddField(
            model_name='ticket',
            name='prioridad',
            field=models.CharField(blank=True, choices=[('baja', 'Baja'), ('media', 'Media'), ('alta', 'Alta'), ('urgente', 'Urgente')], default='media', max_length=10, null=True),
        ),
        migrations.AddField(
            model_name='ticket',
            name='ultima_respuesta',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='ticket',
            name='tipo',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='tickets', to='home.tipoticket'),
        ),
    ]
