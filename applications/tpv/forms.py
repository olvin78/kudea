# tpv/forms.py
from django import forms
from .models import Comanda, Mesa, ComandaItem, Empleado
from applications.product.models import Producto, Categoria

class ComandaForm(forms.ModelForm):
    class Meta:
        model = Comanda
        fields = ['mesa']

    mesa = forms.ModelChoiceField(queryset=Mesa.objects.filter(estado='libre'))  # Solo mesas libres

class ComandaItemForm(forms.ModelForm):
    class Meta:
        model = ComandaItem
        fields = ['producto', 'cantidad']

    producto = forms.ModelChoiceField(queryset=Producto.objects.all(), required=True)
    cantidad = forms.IntegerField(min_value=1, initial=1)





class EmpleadoForm(forms.ModelForm):
    class Meta:
        model = Empleado
        fields = [
            'nombre', 'apellidos', 'nif', 'usuario', 'email',
            'telefono', 'movil', 'direccion', 'cp', 'poblacion', 'provincia',
            'es_administrador', 'puede_realizar_salidas', 'puede_cambiar_fecha_hora',
            'puede_modificar_ventas', 'puede_cambiar_subtotales', 'puede_cambiar_tarifa',
            'esta_de_baja', 'fecha_baja', 'observaciones'
        ]
        widgets = {
            'fecha_baja': forms.DateInput(attrs={
                'type': 'date',
                'class': 'form-control',
                'placeholder': 'Fecha de baja'
            }),
            'observaciones': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Observaciones'
            })
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        for name, field in self.fields.items():
            if name in ['fecha_baja', 'observaciones']:
                continue  # ya están estilizados
            if isinstance(field.widget, forms.CheckboxInput):
                field.widget.attrs.update({
                    'class': 'form-check-input'
                })
            elif isinstance(field.widget, forms.Select):
                field.widget.attrs.update({
                    'class': 'form-select'
                })
            else:
                field.widget.attrs.update({
                    'class': 'form-control',
                    'placeholder': field.label
                })

        # Etiquetas más limpias (opcional)
        self.fields['es_administrador'].label = "Administrador"
        self.fields['puede_realizar_salidas'].label = "Puede realizar salidas"
        self.fields['puede_cambiar_fecha_hora'].label = "Puede cambiar fecha/hora"
        self.fields['puede_modificar_ventas'].label = "Puede modificar ventas"
        self.fields['puede_cambiar_subtotales'].label = "Puede cambiar subtotales"
        self.fields['puede_cambiar_tarifa'].label = "Puede cambiar tarifa"
        self.fields['esta_de_baja'].label = "Empleado de baja"














