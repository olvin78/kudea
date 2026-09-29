from django import forms
from .models import AperturaCaja


class AperturaCajaForm(forms.ModelForm):
    class Meta:
        model = AperturaCaja
        fields = ['fondo_inicial', 'notas']
        labels = {
            'fondo_inicial': 'Fondo inicial',
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


class CierreCajaForm(forms.Form):
    """Arqueo al cierre: dinero contado físicamente en el cajón."""
    efectivo_contado = forms.DecimalField(
        min_value=0, max_digits=10, decimal_places=2,
        widget=forms.NumberInput(attrs={
            'class': 'cierre-input',
            'placeholder': '0.00',
            'min': '0',
            'step': '0.01',
            'autofocus': True,
        }),
    )
    notas = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'cierre-textarea',
            'rows': 2,
            'placeholder': 'Incidencias del turno (opcional)...',
        }),
    )
