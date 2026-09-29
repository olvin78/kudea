# applications/recordlog/views.py
from django.views.generic import TemplateView
from django.contrib.admin.models import LogEntry


class RecordOrderView(TemplateView):
    """Historial de auditoría: acciones registradas por Django (admin + edición)."""

    template_name = "recordlog/record_order.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        qs = LogEntry.objects.select_related("user", "content_type").order_by("-action_time")
        context["registros"] = qs[:200]
        context["total_registros"] = LogEntry.objects.count()
        return context
