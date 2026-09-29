from .roles import get_role, ROLES


def role_context(request):
    """Expone el rol del usuario a todas las plantillas para ocultar botones."""
    rol = get_role(getattr(request, "user", None))
    return {
        "user_role": rol,
        "user_role_label": ROLES.get(rol, ""),
        "es_admin": rol == "admin",
        "es_reportero": rol in ("admin", "gerente"),   # ve informes/finanzas
        "es_operador": rol in ("admin", "gerente", "cajero"),  # cobra/cierra
    }
