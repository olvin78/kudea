# =====================================================================
# 📁 VISTAS · APP 'attendance' — Fichajes (táctil/QR), historial mensual y NÓMINA
# =====================================================================
#   L24    class EmployeeListView(ListView):
#   L46    class EmployeeDetailView(DetailView):
#   L51    class PunchCreateView(CreateView):
#   L63    class PunchView(View):
#   L96    class QRListView(TemplateView):
#   L105   class QRScanView(TemplateView):
#   L108   class QRTokenPunchView(View):
#   L126   class FichajeTouchMenuView(TemplateView):
#   L129   class BuscarHistorialView(View):
#   L141   class EmployeeMonthlyReportView(TemplateView):
#   L250   def verificar_password(request):
#   L280   def _rango_mes(mes):
#   L301   def _filas_nomina(desde, hasta):
#   L332   def NominaView(request):
#   L359   def exportar_nomina_csv(request):
#   L378   def parte_nuevo(request):
#   L410   def parte_borrar(request, pk):
# =====================================================================

from django.shortcuts import render, get_object_or_404, redirect
from django.views import View
from django.views.generic import ListView, DetailView, CreateView, TemplateView
from django.urls import reverse_lazy, reverse
from django.utils.timezone import localdate
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


# ============================================================
#  NÓMINA LIGERA — partes de horas × tarifa
#    · GET  /attendance/nomina/?mes=YYYY-MM  → resumen del mes
#    · GET  /attendance/nomina/exportar/     → CSV
#    · GET/POST /attendance/nomina/parte/nuevo/
#    · POST /attendance/nomina/parte/<pk>/borrar/
# ============================================================
import csv as _csv
from datetime import date

from django.http import HttpResponse
from django.db.models import Sum, F
from django.contrib import messages

from applications.config.roles import role_required
from .models import ParteHoras
from .forms import ParteHorasForm


def _rango_mes(mes):
    """'YYYY-MM' → (desde, hasta_exclusivo, etiqueta_mes_siguiente, etiqueta_mes_anterior)."""
    hoy = localdate()
    try:
        year, month = (int(x) for x in mes.split("-"))
        if not 1 <= month <= 12:
            raise ValueError
    except Exception:
        year, month = hoy.year, hoy.month
    desde = date(year, month, 1)
    if month == 12:
        hasta, ny, nm = date(year + 1, 1, 1), year + 1, 1
    else:
        hasta, ny, nm = date(year, month + 1, 1), year, month + 1
    if month == 1:
        pa = f"{year - 1:04d}-12"
    else:
        pa = f"{year:04d}-{month - 1:02d}"
    return desde, hasta, f"{ny:04d}-{nm:02d}", pa


def _filas_nomina(desde, hasta):
    """Horas e importe por empleado; el importe usa la tarifa congelada de cada parte."""
    from decimal import Decimal

    grupos = (
        ParteHoras.objects.filter(fecha__gte=desde, fecha__lt=hasta)
        .values(
            "employee_id", "employee__nombre", "employee__apellidos",
            "employee__tarifa_hora", "tarifa_hora",
        )
        .annotate(horas=Sum("horas"))
    )
    por_emp = {}
    for g in grupos:
        e = por_emp.get(g["employee_id"])
        if e is None:
            e = por_emp[g["employee_id"]] = {
                "employee_id": g["employee_id"],
                "employee__nombre": g["employee__nombre"],
                "employee__apellidos": g["employee__apellidos"],
                "employee__tarifa_hora": g["employee__tarifa_hora"],
                "horas": Decimal("0"),
                "importe": Decimal("0"),
            }
        horas = g["horas"] or Decimal("0")
        e["horas"] += horas
        e["importe"] += horas * (g["tarifa_hora"] or Decimal("0"))
    return sorted(por_emp.values(), key=lambda x: x["employee__nombre"] or "")


@role_required("gerente")
def NominaView(request):
    mes = request.GET.get("mes") or localdate().strftime("%Y-%m")
    desde, hasta, mes_sig, mes_ant = _rango_mes(mes)
    partes = (
        ParteHoras.objects.filter(fecha__gte=desde, fecha__lt=hasta)
        .select_related("employee")
        .order_by("fecha", "id")
    )
    filas = _filas_nomina(desde, hasta)
    total_horas = sum(f["horas"] or 0 for f in filas)
    total_importe = sum(f["importe"] or 0 for f in filas)
    context = {
        "mes": mes,
        "mes_sig": mes_sig,
        "mes_ant": mes_ant,
        "filas": filas,
        "partes": partes[:60],
        "total_horas": total_horas,
        "total_importe": total_importe,
        "hay_empleados_sin_tarifa": any(
            f["employee__tarifa_hora"] is None for f in filas
        ),
    }
    return render(request, "attendance/nomina.html", context)


@role_required("gerente")
def exportar_nomina_csv(request):
    mes = request.GET.get("mes") or localdate().strftime("%Y-%m")
    desde, hasta, _, _ = _rango_mes(mes)
    resp = HttpResponse(content_type="text/csv; charset=utf-8")
    resp["Content-Disposition"] = f'attachment; filename="kudea_nomina_{mes}.csv"'
    resp.write("\ufeff")
    w = _csv.writer(resp, delimiter=";")
    w.writerow(["empleado", "horas", "importe"])
    total_h = total_i = 0
    for f in _filas_nomina(desde, hasta):
        nombre = f"{f['employee__nombre']} {f['employee__apellidos'] or ''}".strip()
        w.writerow([nombre, f["horas"], f["importe"]])
        total_h += f["horas"] or 0
        total_i += f["importe"] or 0
    w.writerow(["TOTAL", total_h, total_i])
    return resp


@role_required("gerente")
def parte_nuevo(request):
    if request.method == "POST":
        form = ParteHorasForm(request.POST)
        if form.is_valid():
            parte = form.save(commit=False)
            if parte.tarifa_hora is None and parte.employee.tarifa_hora is not None:
                parte.tarifa_hora = parte.employee.tarifa_hora
            parte.save()
            messages.success(
                request,
                f"Parte registrado: {parte.horas} h de {parte.employee} el {parte.fecha}.",
            )
            return redirect(
                reverse("home_attendance:nomina")
                + f"?mes={parte.fecha.strftime('%Y-%m')}"
            )
    else:
        form = ParteHorasForm(initial={"fecha": localdate().isoformat()})
    from applications.employee.models import Employee
    import json
    tarifas = {
        str(e.pk): str(e.tarifa_hora)
        for e in Employee.objects.filter(tarifa_hora__isnull=False)
    }
    return render(
        request,
        "attendance/parte_form.html",
        {"form": form, "tarifas_json": json.dumps(tarifas)},
    )


@role_required("gerente")
def parte_borrar(request, pk):
    parte = get_object_or_404(ParteHoras, pk=pk)
    if request.method == "POST":
        mes = parte.fecha.strftime("%Y-%m")
        parte.delete()
        messages.success(request, "Parte de horas eliminado.")
        return redirect(f"{reverse('home_attendance:nomina')}?mes={mes}")
    return redirect("home_attendance:nomina")
