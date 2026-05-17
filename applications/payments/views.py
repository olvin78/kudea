from django.views.generic import TemplateView, View
from django.contrib.admin.views.decorators import staff_member_required
from django.utils.decorators import method_decorator
from django.shortcuts import get_object_or_404, redirect
from django.contrib import messages
from .models import MetodoPago
from .forms import MetodoPagoForm


class PaymentMethodsView(TemplateView):
    template_name = 'payments/payment_methods.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form'] = MetodoPagoForm()
        context['formas_pago'] = MetodoPago.objects.all()
        return context

    def post(self, request, *args, **kwargs):
        form = MetodoPagoForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, 'Método de pago añadido correctamente.')
            return redirect('payments_app:payment_methods')
        context = self.get_context_data()
        context['form'] = form
        return self.render_to_response(context)


@method_decorator(staff_member_required(login_url='/admin/login/'), name='dispatch')
class DeletePaymentMethodView(View):
    """Solo los administradores (staff) pueden eliminar métodos de pago."""

    def post(self, request, pk, *args, **kwargs):
        metodo = get_object_or_404(MetodoPago, pk=pk)
        nombre = metodo.nombre
        metodo.delete()
        messages.success(request, f'Método de pago "{nombre}" eliminado correctamente.')
        return redirect('payments_app:payment_methods')


@method_decorator(staff_member_required(login_url='/admin/login/'), name='dispatch')
class UpdatePaymentMethodView(View):
    """Solo los administradores (staff) pueden modificar métodos de pago."""

    def post(self, request, pk, *args, **kwargs):
        metodo = get_object_or_404(MetodoPago, pk=pk)
        form = MetodoPagoForm(request.POST, request.FILES, instance=metodo)
        if form.is_valid():
            form.save()
            messages.success(request, f'Método de pago "{metodo.nombre}" actualizado correctamente.')
        else:
            messages.error(request, 'Error al actualizar el método de pago.')
        return redirect('payments_app:payment_methods')
