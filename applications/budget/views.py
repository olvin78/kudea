from django.views.generic import TemplateView, DetailView, ListView, UpdateView, ListView, CreateView
from django.db.models import Q
from django.shortcuts import render
from django.db.models import Count, Sum
from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse
from django.urls import reverse_lazy  # ✅ Corrección aquí
from .models import Client, Budget, BudgetItem
from .forms import BudgetForm, BudgetItemFormSet, ClientForm
from django.contrib.auth.mixins import UserPassesTestMixin
from django.contrib import messages




class BudgetMainView(TemplateView):
    template_name = "budget/budget_home.html"



class BudgetCreateView(CreateView):
    model = Budget
    form_class = BudgetForm
    template_name = 'budget/presupuesto.html'
    success_url = reverse_lazy('budget_app:budget_list')  # cámbialo según tu proyecto

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.POST:
            context['item_formset'] = BudgetItemFormSet(self.request.POST)
        else:
            context['item_formset'] = BudgetItemFormSet(queryset=BudgetItem.objects.none())
        return context

    def form_valid(self, form):
        context = self.get_context_data()
        item_formset = context['item_formset']

        if item_formset.is_valid():
            self.object = form.save()  # Guardamos el presupuesto

            # Guardamos los ítems asociados
            item_formset.instance = self.object
            item_formset.save()

            # Calculamos el total con impuestos y lo guardamos
            self.object.total = self.object.calcular_total_con_impuestos
            self.object.save()

            return redirect('budget_app:budget_detail', pk=self.object.id)
        else:
            return self.form_invalid(form)
    


def delete_budget_item(request, item_id):
    item = get_object_or_404(BudgetItem, id=item_id)
    item.delete()
    return redirect('create_budget') 



def add_client(request):
    if request.method == 'POST':
        form = ClientForm(request.POST)
        if form.is_valid():
            form.save()  # ✅ Guarda el cliente en la base de datos
            return redirect('budget_app:crear.html')  # ✅ Redirige tras guardar
    else:
        form = ClientForm()

    clientes = Client.objects.all()  # ✅ Obtiene todos los clientes para la búsqueda

    return render(request, 'budget/add_client.html', {
        'form': form,
        'clientes': clientes  # ✅ Pasamos los clientes para el filtro
    })



def budget_success(request, pk):
    """Vista de éxito después de crear un presupuesto"""
    budget = get_object_or_404(Budget, pk=pk)  # ✅ Obtiene el presupuesto usando el pk
    return redirect('budget_app:budget_detail', pk=budget.id)





class BudgetUpdateView(UpdateView):
    model = Budget
    form_class = BudgetForm
    template_name = "budget/budget_form.html"
    success_url = reverse_lazy('budget_app:budget_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.POST:
            context['item_formset'] = BudgetItemFormSet(self.request.POST, instance=self.object)
        else:
            context['item_formset'] = BudgetItemFormSet(instance=self.object)
        return context

    def form_valid(self, form):
        context = self.get_context_data()
        item_formset = context['item_formset']

        if form.is_valid() and item_formset.is_valid():
            self.object = form.save()

            items = item_formset.save(commit=False)
            for item in items:
                item.presupuesto = self.object
                item.save()

            for deleted_item in item_formset.deleted_objects:
                deleted_item.delete()

            total = sum(item.subtotal for item in self.object.items.all())
            self.object.total = total
            self.object.save()

            return super().form_valid(form)

        return self.form_invalid(form)





class BudgetListView(ListView):
    model = Budget
    template_name = "budget/budget_list.html"
    context_object_name = "budgets"

    def get_queryset(self):
        queryset = super().get_queryset().exclude(id__isnull=True)
        query = self.request.GET.get('q')
        if query:
            queryset = queryset.filter(
                Q(cliente__nombre__icontains=query) |
                Q(id__iexact=query)
            )
        return queryset.order_by('-id')




class BudgetDetailView(DetailView):
    model = Budget
    template_name = "budget/budget_detail.html"
    context_object_name = "budget"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        budget = self.get_object()
        context["subtotal"] = budget.calcular_subtotal
        context["impuestos"] = budget.calcular_impuestos
        context["total_con_impuestos"] = budget.calcular_total_con_impuestos
        context["items"] = budget.items.all()
        return context
