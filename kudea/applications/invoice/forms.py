from django import forms
from django.forms.models import inlineformset_factory
from .models import Factura, ItemFactura


class FacturaForm(forms.ModelForm):
    class Meta:
        model = Factura
        exclude = [
            'numero', 'creada_por', 'modificada_por',
            'creada_en', 'modificada_en', 'total', 'total_iva',
            'total_irpf', 'total_recargo', 'subtotal', 'base_imponible'
        ]
        widgets = {
            'fecha_emision': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'fecha_vencimiento': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'fecha_pago': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'cliente_direccion': forms.Textarea(attrs={'rows': 2, 'class': 'form-control'}),
            'emisor_direccion': forms.Textarea(attrs={'rows': 2, 'class': 'form-control'}),
            'leyenda_factura': forms.Textarea(attrs={'rows': 2, 'class': 'form-control'}),
            'notas_internas': forms.Textarea(attrs={'rows': 2, 'class': 'form-control'}),
        }


class ItemFacturaForm(forms.ModelForm):
    class Meta:
        model = ItemFactura
        fields = [
            'producto', 'descripcion', 'referencia',
            'cantidad', 'unidad_medida', 'precio_unitario',
            'descuento', 'tipo_iva', 'notas'
        ]
        widgets = {
            'descripcion': forms.TextInput(attrs={'class': 'form-control'}),
            'referencia': forms.TextInput(attrs={'class': 'form-control'}),
            'cantidad': forms.NumberInput(attrs={'step': '0.01', 'class': 'form-control'}),
            'precio_unitario': forms.NumberInput(attrs={'step': '0.01', 'class': 'form-control'}),
            'descuento': forms.NumberInput(attrs={'step': '0.01', 'class': 'form-control'}),
            'unidad_medida': forms.TextInput(attrs={'class': 'form-control'}),
            'tipo_iva': forms.Select(attrs={'class': 'form-control'}),
            'notas': forms.Textarea(attrs={'rows': 1, 'class': 'form-control'}),
        }


ItemFacturaInlineFormset = inlineformset_factory(
    Factura,
    ItemFactura,
    form=ItemFacturaForm,
    extra=1,
    can_delete=True
)
