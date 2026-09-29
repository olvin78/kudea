from django import forms
from django.utils.timezone import localdate
from .models import Punch, ParteHoras

class PunchForm(forms.ModelForm):
    class Meta:
        model = Punch
        fields = ['clock_in', 'clock_out']


class ParteHorasForm(forms.ModelForm):
    """Alta de horas para nómina; precarga la tarifa del empleado."""

    class Meta:
        model = ParteHoras
        fields = ["employee", "fecha", "horas", "tarifa_hora", "notas"]
        widgets = {
            "fecha": forms.DateInput(
                attrs={"type": "date", "class": "form-control"}
            ),
            "employee": forms.Select(attrs={"class": "form-select"}),
            "horas": forms.NumberInput(
                attrs={"class": "form-control", "step": "0.25", "min": "0", "max": "24"}
            ),
            "tarifa_hora": forms.NumberInput(
                attrs={"class": "form-control", "step": "0.01", "min": "0"}
            ),
            "notas": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "Opcional"}
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["fecha"].required = False
        self.fields["horas"].label = "Horas"
        self.fields["tarifa_hora"].label = "Tarifa €/h"
        self.fields["notas"].label = "Notas"
        if not self.instance.pk:
            self.fields["fecha"].initial = localdate()

    def clean_horas(self):
        horas = self.cleaned_data["horas"]
        if horas <= 0 or horas > 24:
            raise forms.ValidationError("Introduce entre 0.25 y 24 horas.")
        return horas
