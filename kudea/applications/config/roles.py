"""
Roles de KUDEA — 4 niveles, simples y directos:

  admin    → TODO (configuración, usuarios, informes, finanzas)
  gerente  → informes, compras, finanzas, anular ventas, editar productos
  cajero   → vender, cobrar fiado, abrir/cerrar su caja (NO ve costes ni informes)
  vista    → solo lectura de paneles (no cobra ni cierra caja)

Usuarios súper/staff de Django = admin siempre.
Usuario sin grupo asignado = cajero (por defecto operativo).
"""
from functools import wraps
from django.conf import settings
from django.shortcuts import redirect

ROLES = {
    "admin": "Administrador",
    "gerente": "Gerente",
    "cajero": "Cajero",
    "vista": "Solo lectura",
}

DEFAULT_ROLE = "cajero"
# Orden de "poder" para comprobaciones (admin cubre todo)
ROLE_RANK = {"admin": 3, "gerente": 2, "cajero": 1, "vista": 0}


def get_role(user):
    """Devuelve el rol efectivo del usuario ('admin'/'gerente'/'cajero'/'vista' o None)."""
    if user is None or not user.is_authenticated:
        return None
    if user.is_superuser or user.is_staff:
        return "admin"
    for g in user.groups.values_list("name", flat=True):
        if g in ROLES:
            return g
    return DEFAULT_ROLE


def role_at_least(role, minimum):
    return ROLE_RANK.get(role, -1) >= ROLE_RANK.get(minimum, 99)


def role_required(*roles):
    """
    Decorador para vistas (CBV as_view() o funciones).
    admin pasa siempre; si tu rol está en la lista, pasa; si no, mensaje + inicio.
    """
    def decorator(view):
        @wraps(view)
        def wrapper(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect(settings.LOGIN_URL)
            rol = get_role(request.user)
            if rol == "admin" or rol in roles:
                return view(request, *args, **kwargs)
            from django.contrib import messages
            messages.error(
                request,
                "No tienes permisos para esta sección con el rol "
                f"«{ROLES.get(rol, rol)}». Contacta con el administrador.",
            )
            return redirect("/")
        return wrapper
    return decorator


def ensure_groups():
    """Crea los grupos (roles) si no existen. Idempotente."""
    from django.contrib.auth.models import Group
    for key, label in ROLES.items():
        if key == "admin":
            continue  # admin = súper/staff, no necesita grupo
        Group.objects.get_or_create(name=key)
