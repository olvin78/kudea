from django.urls import path
from .views import DashboardPrincipalView  # ← ESTE ES EL NOMBRE REAL

app_name = "reporting_app"

urlpatterns = [
    path('', DashboardPrincipalView.as_view(), name="dashboard_informes"),
]