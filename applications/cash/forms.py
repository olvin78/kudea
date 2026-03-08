from django import forms
from .models import AperturaCaja


class AperturaCajaForm(forms.ModelForm):
    class Meta:
        model = AperturaCaja
        fields = ['fondo_inicial', 'notas']
        labels = {
            'fondo_inicial': 'Fondo inicial (€)',
            'notas': 'Notas de apertura',
        }
        widgets = {
            'fondo_inicial': forms.NumberInput(attrs={
                'class': 'form-control form-control-lg',
                'placeholder': '0.00',
                'min': '0',
                'step': '0.01',
                'autofocus': True,
            }),
            'notas': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': 'Observaciones opcionales...',
            }),
        }
