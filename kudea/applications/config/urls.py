# =====================================================================
# 📁 RUTAS · APP 'config'  (CONFIGURACIÓN TRANSVERSAL)
# URL base: /config/…
#   · Roles (gerente/cajero/vista), configuración fiscal, BACKUP BD
#   · Módulos on/off viven en home.Modulo (sección en home/models)
# =====================================================================

from django.urls import path
from applications.config.roles import role_required
from applications.config.views import ConfiguracionesView, RefreshPinView, UsuariosRolesView, BackupView, backup_descargar

A = role_required()

urlpatterns = [
    path('', A(ConfiguracionesView.as_view()), name='configuraciones'),
    path('refresh-pin/<int:caja_id>/', A(RefreshPinView.as_view()), name='refresh_pin'),
    path('usuarios/', A(UsuariosRolesView.as_view()), name='usuarios_roles'),
    path('backup/', A(BackupView.as_view()), name='backup_datos'),
    path('backup/descargar/', A(backup_descargar), name='backup_descargar'),
]
