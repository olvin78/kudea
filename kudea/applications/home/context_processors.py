from applications.home.models import Comunicacion, Modulo

def modulos_activos(request):
    """
    Inyecta el estado de los módulos en todas las plantillas
    """
    modulos = Modulo.objects.all()
    context_modulos = {}
    for m in modulos:
        context_modulos[m.clave] = m.activo
    return {'MODULOS': context_modulos}

def comunicaciones_context(request):
    if request.user.is_authenticated:
        comunicaciones = Comunicacion.objects.all()[:20]
        unread_comms = Comunicacion.objects.exclude(visto_por=request.user).count()
        return {
            'comunicaciones': comunicaciones,
            'unread_comms': unread_comms
        }
    return {}