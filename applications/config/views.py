import json
import os
from django.shortcuts import render
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views import View


class ConfiguracionesView(LoginRequiredMixin, View):
    template_name = 'config/configuraciones.html'

    def get(self, request):
        alertas = []
        try:
            base_dir = os.path.dirname(os.path.abspath(__file__))
            anomalies_path = os.path.join(base_dir, '../home/anomalies.json')
            anomalies_path = os.path.normpath(anomalies_path)
            if os.path.exists(anomalies_path):
                with open(anomalies_path, 'r', encoding='utf-8') as f:
                    alertas = json.load(f)
        except Exception:
            pass

        context = {
            'alertas': alertas,
            'total_alertas': len(alertas),
        }
        return render(request, self.template_name, context)
