# applications/recordlog/urls.py
from django.urls import path
from .views import RecordOrderView  # Asegúrate de que exista esta vista

app_name = 'recordlog_app'

urlpatterns = [
    path('', RecordOrderView.as_view(), name='record_order'),
]
