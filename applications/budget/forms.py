from django import forms
from django.forms import inlineformset_factory
from .models import Budget, BudgetItem, Client

# ✅ Formulario para el Presupuesto (Budget)
class BudgetForm(forms.ModelForm):
    class Meta:
        model = Budget
        fields = ['cliente', 'descripcion', 'total']
        widgets = {
            'cliente': forms.Select(attrs={'class': 'form-control'}),
            'descripcion': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'total': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
        }

# ✅ Formulario para los Ítems del Presupuesto (BudgetItem)
class BudgetItemForm(forms.ModelForm):
    class Meta:
        model = BudgetItem
        fields = ['descripcion', 'cantidad', 'precio_unitario', 'descuento']  # Incluyendo descuento
        widgets = {
            'descripcion': forms.TextInput(attrs={'class': 'form-control'}),
            'cantidad': forms.NumberInput(attrs={'class': 'form-control', 'min': '1'}),
            'precio_unitario': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'descuento': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),  # Campo descuento
        }

# ✅ Formulario para el Cliente (Client)
class ClientForm(forms.ModelForm):
    class Meta:
        model = Client
        fields = ['nombre', 'empresa', 'nif', 'email', 'telefono', 'direccion', 'ciudad', 'codigo_postal']
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control'}),
            'empresa': forms.TextInput(attrs={'class': 'form-control'}),
            'nif': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'telefono': forms.TextInput(attrs={'class': 'form-control'}),
            'direccion': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'ciudad': forms.TextInput(attrs={'class': 'form-control'}),
            'codigo_postal': forms.TextInput(attrs={'class': 'form-control'}),
        }

# ✅ Formset para manejar múltiples ítems en un presupuesto
BudgetItemFormSet = inlineformset_factory(
    Budget,
    BudgetItem,
    fields=['descripcion', 'cantidad', 'precio_unitario', 'descuento'],
    extra=1,
    can_delete=True
)


class BudgetForm(forms.ModelForm):
    class Meta:
        model = Budget
        fields = ['cliente', 'agente', 'descripcion', 'impuesto_porcentaje']
        widgets = {
            'cliente': forms.Select(attrs={'class': 'form-control'}),
            'agente': forms.Select(attrs={'class': 'form-control'}),
            'descripcion': forms.Textarea(attrs={'class': 'form-control'}),
            'impuesto_porcentaje': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
        }


