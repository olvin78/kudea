from django.shortcuts import render
from django.views.generic import TemplateView

from django.views.generic import TemplateView

class TpvIndexView(TemplateView):
    template_name = 'tpv/index.html'

class TpvMesasView(TemplateView):
    template_name = 'tpv/mesas.html'

class TpvComandasView(TemplateView):
    template_name = 'tpv/comandas.html'

class TpvCobrosView(TemplateView):
    template_name = 'tpv/cobros.html'

class TpvHistorialView(TemplateView):
    template_name = 'tpv/historial.html'

class TpvConfigView(TemplateView):
    template_name = 'tpv/config.html'
