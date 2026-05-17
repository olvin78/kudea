from django.views.generic import ListView, UpdateView, CreateView
from .models import Employee
from . forms import EmployeeForm
from django.urls import reverse_lazy


class EmployeeCreateView(CreateView):
    model = Employee
    form_class = EmployeeForm
    template_name = 'employee/employee_create.html'
    success_url = reverse_lazy('employee_app:employee_list')

    


# Vista para mostrar la lista de empleados
class EmployeeListView(ListView):
    model = Employee
    template_name = 'employee/employee_list.html'  # Asegúrate de que la plantilla exista
    context_object_name = 'employee'
    paginate_by = 10  # Si deseas paginación




# Vista para editar un empleado

class EmployeeUpdateView(UpdateView):
    model = Employee
    form_class = EmployeeForm
    template_name = 'employee/employee_edit.html'
    success_url = reverse_lazy('employee_app:employee_list')


    def form_valid(self, form):
        # Asignar user si no viene en POST (solo si tiene sentido)
    
        form.instance.user = self.request.user  # o quien corresponda
        return super().form_valid(form)


"""
class EmployeeListView(TemplateView):
    template_name = 'employee/employee_list.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['empleados'] = Employee.objects.all()
        return context




class EmpleadoCreateView(CreateView):
    model = Employee
    form_class = EmployeeForm
    template_name = 'employee/empleado_create.html'
    success_url = reverse_lazy('employee_app:employee_list')

    def form_valid(self, form):
        empleado = form.save(commit=False)
        empleado.user = self.request.user  # o cualquier lógica para asignar un User
        empleado.save()
        return super().form_valid(form)




# Vista para mostrar la lista de empleados
class EmpleadoListView(ListView):
    model = Employee
    template_name = 'tpv/empleados_lista.html'  # Asegúrate de que la plantilla exista
    context_object_name = 'empleados'
    paginate_by = 10  # Si deseas paginación



# Vista para editar un empleado
class EmpleadoUpdateView(UpdateView):
    model = Employee
    form_class = EmployeeForm
    template_name = 'tpv/editar_empleado.html'  # Asegúrate de que la plantilla exista
    context_object_name = 'empleado'

    def get_success_url(self):
        return reverse_lazy('tpv_app:empleados_lista')  # Redirige a la lista de empleados tras guardar"""