from .models import Modulo

def modulos_activos(request):
    modulos = {
        m.clave: m.activo
        for m in Modulo.objects.all()
    }
    return {"MODULOS": modulos}