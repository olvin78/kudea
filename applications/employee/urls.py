from django.urls import path
from .views import EmployeeListView, EmployeeCreateView, EmployeeUpdateView

app_name = 'employee_app'

urlpatterns = [
    path('', EmployeeListView.as_view(), name='employee_list'),  # o elimina si no la usas
    path('employee/new/', EmployeeCreateView.as_view(), name='employee_create'),
    path('employee/<int:pk>/editar/', EmployeeUpdateView.as_view(), name='editar_empleado'),



    # --- EMPLEADOS ---
    # path('empleados_nuevo/', EmpleadoCreateView.as_view(), name='empleado_create'),
    #path('empleados/<int:pk>/editar/', EmpleadoUpdateView.as_view(), name='editar_empleado'),
]
