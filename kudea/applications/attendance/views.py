from django.shortcuts import render, get_object_or_404, redirect
from django.views import View
from django.views.generic import ListView, DetailView, CreateView, TemplateView
from django.urls import reverse_lazy
from django.utils import timezone
from django.contrib import messages

from .models import Employee, Punch
from .forms import PunchForm
from calendar import monthrange
from types import SimpleNamespace

from collections import defaultdict
from django.db.models import Q


from django.contrib.auth import authenticate
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt



class EmployeeListView(ListView):
    model = Employee
    template_name = 'home_attendance/employee_list.html'
    context_object_name = 'empleados'
    paginate_by = 10  # Muestra 10 por página

    def get_queryset(self):
        query = self.request.GET.get('q')
        queryset = super().get_queryset().select_related('user')
        if query:
            queryset = queryset.filter(
                Q(user__first_name__icontains=query) |
                Q(user__last_name__icontains=query) |
                Q(user__username__icontains=query)
            )
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['q'] = self.request.GET.get('q', '')
        return context

class EmployeeDetailView(DetailView):
    model = Employee
    template_name = 'attendance/employee_detail.html'
    context_object_name = 'employee'

class PunchCreateView(CreateView):
    model = Punch
    form_class = PunchForm
    template_name = 'attendance/punch_form.html'

    def form_valid(self, form):
        form.instance.employee_id = self.kwargs['pk']
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy('attendance:employee_detail', kwargs={'pk': self.kwargs['pk']})

class PunchView(View):
    def get(self, request):
        return render(request, 'attendance/punch_screen.html')

    def post(self, request):
        code = request.POST.get('code')
        try:
            employee = Employee.objects.get(codigo=code)
        except Employee.DoesNotExist:
            return render(request, 'attendance/punch_screen.html', {'error': 'Código inválido'})

        now = timezone.now()
        last_punch = Punch.objects.filter(
            employee=employee,
            clock_out__isnull=True
        ).order_by('-clock_in').first()

        if last_punch:
            # Registrar salida (si hay un punch sin clock_out)
            last_punch.clock_out = now
            last_punch.save()
            status = 'Salida registrada'
        else:
            # Registrar entrada
            Punch.objects.create(employee=employee, clock_in=now)
            status = 'Entrada registrada'

        return render(request, 'attendance/punch_screen.html', {
            'employee': employee,
            'status': status,
            'last_punch': Punch.objects.filter(employee=employee).order_by('-clock_in').first()
        })

class QRListView(TemplateView):
    template_name = "attendance/qr_list.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        from .models import Employee
        context['employees'] = Employee.objects.exclude(qr_token__isnull=True)
        return context

class QRScanView(TemplateView):
    template_name = "attendance/fichaje_qr.html"

class QRTokenPunchView(View):
    def get(self, request, token):
        employee = get_object_or_404(Employee, qr_token=token)
        now = timezone.now()

        last_punch = Punch.objects.filter(employee=employee).order_by('-clock_in').first()

        if last_punch and not last_punch.clock_out:
            last_punch.clock_out = now
            last_punch.save()
            msg = "Salida registrada"
        else:
            Punch.objects.create(employee=employee, clock_in=now)
            msg = "Entrada registrada"

        messages.success(request, f"{employee.user.get_full_name()}: {msg}")
        return redirect("home_attendance:fichaje_menu")

class FichajeTouchMenuView(TemplateView):
    template_name = "attendance/fichaje_touch_menu.html"

class BuscarHistorialView(View):
    def post(self, request):
        code = request.POST.get("code")
        try:
            employee = Employee.objects.get(codigo=code)
            return redirect('home_attendance:employee_monthly_report', pk=employee.pk)
        except Employee.DoesNotExist:
            return render(request, "attendance/fichaje_touch_menu.html", {
                "error": "Código no válido"
            })


class EmployeeMonthlyReportView(TemplateView):
    template_name = "attendance/employee_monthly_report.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        employee_id = self.kwargs.get('pk')
        employee = get_object_or_404(Employee, pk=employee_id)
        now = timezone.now()

        today = now.date()
        first_day = today.replace(day=1)
        last_day = today.replace(day=monthrange(today.year, today.month)[1])

        punches = Punch.objects.filter(
            employee=employee,
            clock_in__date__gte=first_day,
            clock_in__date__lte=last_day
        ).order_by('clock_in')

        complete_records = 0
        incomplete_records = 0
        punches_list = []
        week_totals = {}
        month_total_seconds = 0
        
        for punch in punches:
            week_number = punch.clock_in.isocalendar()[1]
            is_active = not punch.clock_out
            
            if punch.clock_out:
                time_difference = punch.clock_out - punch.clock_in
                total_seconds = int(time_difference.total_seconds())
                complete_records += 1
            else:
                time_difference = now - punch.clock_in
                total_seconds = int(time_difference.total_seconds())
                incomplete_records += 1

            # Formatear a HH:MM:SS
            hours = total_seconds // 3600
            minutes = (total_seconds % 3600) // 60
            seconds = total_seconds % 60
            hours_worked = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
            
            # Acumular por semana y mensual
            if week_number not in week_totals:
                week_totals[week_number] = 0
            week_totals[week_number] += total_seconds
            month_total_seconds += total_seconds
            
            punches_list.append({
                'punch': punch,
                'hours_worked': hours_worked,
                'week_number': week_number,
                'is_active': is_active
            })

        # Asegurar que todas las semanas tengan al menos 00:00:00
        all_weeks = set(punch.clock_in.isocalendar()[1] for punch in punches if punch.clock_in)
        for week in all_weeks:
            if week not in week_totals:
                week_totals[week] = 0

        # Formatear totales
        def format_seconds(seconds):
            hours = seconds // 3600
            minutes = (seconds % 3600) // 60
            seconds = seconds % 60
            return f"{hours:02d}:{minutes:02d}:{seconds:02d}"

        formatted_week_totals = {
            week: format_seconds(seconds) 
            for week, seconds in week_totals.items()
        }
        monthly_total = format_seconds(month_total_seconds)

        # Resumen Anual para la tabla tipo Seguridad Social
        annual_punches = Punch.objects.filter(
            employee=employee,
            clock_in__year=now.year
        )
        annual_seconds = {m: 0 for m in range(1, 13)}
        for p in annual_punches:
            if p.clock_out:
                duration = (p.clock_out - p.clock_in).total_seconds()
                annual_seconds[p.clock_in.month] += int(duration)
        
        annual_summary = {m: format_seconds(s) for m, s in annual_seconds.items()}

        context.update({
            'employee': employee,
            'punches': punches_list or [{'hours_worked': '00:00:00'}],  # Valor por defecto
            'first_day': first_day,
            'last_day': last_day,
            'complete_records': complete_records,
            'incomplete_records': incomplete_records,
            'week_totals': formatted_week_totals or {'1': '00:00:00'},  # Valor por defecto
            'monthly_total': monthly_total or '00:00:00',  # Valor por defecto
            'annual_summary': annual_summary,
            'current_year': now.year,
            'current_time': now
        })
        return context





@csrf_exempt
def verificar_password(request):
    if request.method == 'POST':
        password = request.POST.get('password')
        user = request.user
        if user.is_authenticated and user.is_superuser:
            user_auth = authenticate(username=user.username, password=password)
            if user_auth:
                return JsonResponse({'success': True})
        return JsonResponse({'success': False})
