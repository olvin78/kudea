# applications/tpv_shop/forms.py
from django import forms
from .models import CartItem, CajaArqueo




class EmailForm(forms.Form):
    email = forms.EmailField(
        label='Correo electrónico',
        widget=forms.EmailInput(attrs={'placeholder': 'Introduce tu correo electrónico'})
    )



class CartItemForm(forms.ModelForm):
    class Meta:
        model = CartItem
        fields = ['quantity']



class UpdateCartItemForm(forms.Form):
    quantity = forms.IntegerField(min_value=1, max_value=100)
    item_id = forms.IntegerField(widget=forms.HiddenInput())







class CajaArqueoForm(forms.ModelForm):
    class Meta:
        model = CajaArqueo
        fields = [
            'efectivo_inicial', 'efectivo_final',
            'tarjeta_total', 'bizum_total',
            'total_ventas', 'observaciones'
        ]
        widgets = {
            'efectivo_inicial': forms.NumberInput(attrs={'class': 'form-control'}),
            'tarjeta_total': forms.NumberInput(attrs={'class': 'form-control'}),
            'bizum_total': forms.NumberInput(attrs={'class': 'form-control'}),
            'total_ventas': forms.NumberInput(attrs={'class': 'form-control'}),
            'observaciones': forms.Textarea(attrs={
                'class': 'form-control', 
                'placeholder': 'Observaciones...',
                'rows': 3
            }),
        }