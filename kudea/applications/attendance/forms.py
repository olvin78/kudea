from django import forms
from .models import Punch

class PunchForm(forms.ModelForm):
    class Meta:
        model = Punch
        fields = ['clock_in', 'clock_out']
