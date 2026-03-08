from django import forms
from django.contrib.auth.models import User
from .models import Employee

class EmployeeForm(forms.ModelForm):
    email = forms.EmailField(label='Correo electrónico', required=False)  # <-- AÑADIDO

    class Meta:
        model = Employee
        fields = [
            'user', 'nombre', 'apellidos', 'usuario', 'nif', 'numero_seguridad_social',
            'telefono', 'movil', 'direccion', 'cp', 'poblacion', 'provincia',
            'es_administrador', 'puede_realizar_salidas', 'puede_cambiar_fecha_hora',
            'puede_modificar_ventas', 'puede_cambiar_subtotales', 'puede_cambiar_tarifa',
            'esta_de_baja', 'fecha_baja', 'observaciones', 'nfc_uid'
        ]
        widgets = {
            # ... como ya lo tienes ...
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if self.instance and self.instance.user:
            self.fields['email'].initial = self.instance.user.email


        # Estilizado con clases de Bootstrap
        for name, field in self.fields.items():
            if isinstance(field.widget, forms.CheckboxInput):
                field.widget.attrs.update({'class': 'form-check-input'})
            elif isinstance(field.widget, forms.Select):
                field.widget.attrs.update({'class': 'form-select'})
            elif isinstance(field.widget, forms.DateInput):
                field.widget.attrs.update({'class': 'form-control', 'autocomplete': 'off'})
            else:
                field.widget.attrs.update({'class': 'form-control', 'placeholder': field.label})

        # Etiquetas personalizadas
        self.fields['user'].label = "Usuario vinculado (login)"
        if 'nfc_uid' in self.fields:
            self.fields['nfc_uid'].label = "UID NFC"
        self.fields['numero_seguridad_social'].label = "N.º Seguridad Social"
        self.fields['es_administrador'].label = "Administrador"
        self.fields['puede_realizar_salidas'].label = "Puede realizar salidas"
        self.fields['puede_cambiar_fecha_hora'].label = "Puede cambiar fecha/hora"
        self.fields['puede_modificar_ventas'].label = "Puede modificar ventas"
        self.fields['puede_cambiar_subtotales'].label = "Puede cambiar subtotales"
        self.fields['puede_cambiar_tarifa'].label = "Puede cambiar tarifa"
        self.fields['esta_de_baja'].label = "Empleado de baja"

        # Formato específico para fecha_baja (esto será útil si necesitas JS datepicker)
        self.fields['fecha_baja'].widget = forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Fecha baja',
            'autocomplete': 'off',
            'id': 'id_fecha_baja'
        })

    def save(self, commit=True):
        employee = super().save(commit=False)
        email = self.cleaned_data.get('email')

        if email and employee.user:
            employee.user.email = email
            employee.user.save()

        if commit:
            employee.save()

        return employee





