from django.views.generic import CreateView, ListView, DetailView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.shortcuts import get_object_or_404, redirect, render
from django.contrib import messages

from .models import Factura
from .forms import FacturaForm, ItemFacturaInlineFormset


from django.views.generic.edit import CreateView
from .models import Factura, ItemFactura
from .forms import FacturaForm, ItemFacturaInlineFormset


class FacturaListView(ListView):
    model = Factura
    template_name = 'invoice/invoice_list.html'
    context_object_name = 'facturas'
    paginate_by = 20


class FacturaDetailView(DetailView):
    model = Factura
    template_name = 'invoice/invoice_detail.html'
    context_object_name = 'factura'



class FacturaCreateView(CreateView):
    model = Factura
    form_class = FacturaForm
    template_name = 'invoice/invoice_form.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.POST:
            context['factura_items'] = ItemFacturaInlineFormset(self.request.POST)
        else:
            context['factura_items'] = ItemFacturaInlineFormset()
        return context

    def form_valid(self, form):
        context = self.get_context_data()
        factura_items = context['factura_items']

        # Guardar la factura primero
        self.object = form.save(commit=False)
        self.object.save()

        if factura_items.is_valid():
            factura_items.instance = self.object
            factura_items.save()

        # Recalcular totales una vez que hay ítems
        self.object.calcular_totales()
        return super().form_valid(form)


class FacturaUpdateView(UpdateView):
    model = Factura
    form_class = FacturaForm
    template_name = 'invoice/invoice_form.html'
    success_url = reverse_lazy('invoice_app:invoice_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.POST:
            context['formset'] = ItemFacturaInlineFormset(self.request.POST, instance=self.object)
        else:
            context['formset'] = ItemFacturaInlineFormset(instance=self.object)
        return context

    def form_valid(self, form):
        context = self.get_context_data()
        formset = context['formset']
        if formset.is_valid():
            self.object = form.save(commit=False)
            self.object.modificada_por = self.request.user
            self.object.save()
            formset.instance = self.object
            formset.save()
            messages.success(self.request, "Factura actualizada correctamente.")
            return redirect(self.success_url)
        else:
            return self.render_to_response(self.get_context_data(form=form))


class FacturaDeleteView(DeleteView):
    model = Factura
    template_name = 'invoice/invoice_confirm_delete.html'
    success_url = reverse_lazy('invoice_app:invoice_list')


def anular_factura(request, pk):
    factura = get_object_or_404(Factura, pk=pk)
    factura.estado = 'anulada'
    factura.save()
    messages.success(request, "Factura anulada.")
    return redirect('invoice_app:detalle', pk=pk)
