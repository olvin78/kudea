# applications/recordlog/views.py
from django.views.generic import TemplateView

class RecordOrderView(TemplateView):
    template_name = 'recordlog/record_order.html'
