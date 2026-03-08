from django.urls import path
from . import views
from .views import QRListView, FichajeTouchMenuView, QRTokenPunchView, QRScanView, BuscarHistorialView, EmployeeMonthlyReportView, FichajeTouchMenuView, EmployeeListView

from .views import verificar_password

app_name = 'home_attendance'  # muy bien definido para usar 

urlpatterns = [
    path('', FichajeTouchMenuView.as_view(), name='fichaje_menu'),
    path('employee/<int:pk>/', views.EmployeeDetailView.as_view(), name='employee_detail'),
    path('employee/<int:pk>/punch/', views.PunchCreateView.as_view(), name='punch_create'),
    path('punch/', views.PunchView.as_view(), name='punch'),
    path('qr-codes/', QRListView.as_view(), name='qr_list'),
    path('qr/', QRScanView.as_view(), name='fichaje_qr'),  # 🟢 Abre la cámara y escanea
    path('fichar/<str:token>/', QRTokenPunchView.as_view(), name='qr_fichar'),  # 🟢 Registra la entrada/salida
    path('buscar-historial/', BuscarHistorialView.as_view(), name='buscar_historial'),
    path('employee/<int:pk>/monthly-report/', EmployeeMonthlyReportView.as_view(), name='employee_monthly_report'),
    path('employees/', EmployeeListView.as_view(), name='employee_list'),
    path('verificar-password/', verificar_password, name='verificar_password'),
]