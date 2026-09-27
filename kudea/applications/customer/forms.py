from django import forms
from .models import Cliente

class ClienteForm(forms.ModelForm):
    class Meta:
        model = Cliente
        fields = ['nombre', 'dni', 'codigo_postal', 'correo', 'telefono']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.update({'class': 'form-control'})


# ============================================================
#  FIADO — alta de cliente INDEPENDIENTE (no usa la plantilla
#  de tpv_shop, para no mezclar los dos flujos)
# ============================================================
class ClienteFiadoForm(forms.ModelForm):
    """Alta de cliente desde la pantalla del fiado."""

    class Meta:
        model = Cliente
        fields = ['nombre', 'dni', 'telefono', 'correo']
        widgets = {
            'nombre': forms.TextInput(attrs={
                'class': 'f-input-lg', 'placeholder': 'Nombre y apellido *',
                'autofocus': True,
            }),
            'dni': forms.TextInput(attrs={
                'class': 'f-input-lg', 'placeholder': 'DNI (opcional)',
            }),
            'telefono': forms.TextInput(attrs={
                'class': 'f-input-lg', 'placeholder': 'Teléfono (opcional)',
            }),
            'correo': forms.EmailInput(attrs={
                'class': 'f-input-lg', 'placeholder': 'Correo (opcional)',
            }),
        }

    def clean_nombre(self):
        nombre = (self.cleaned_data.get('nombre') or '').strip()
        if not nombre:
            raise forms.ValidationError('Escribe el nombre del cliente.')
        return nombre