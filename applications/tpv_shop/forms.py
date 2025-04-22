# applications/tpv_shop/forms.py
from django import forms
from .models import CartItem



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