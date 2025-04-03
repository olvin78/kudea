from django import forms
from .models import Ticket

class TicketForm(forms.ModelForm):
    class Meta:
        model = Ticket
        fields = ['campo1', 'campo2', 'campo3']  # Los campos del formulario
