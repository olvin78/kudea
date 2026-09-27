# ============================================================
# FORMULARIOS DEL MÓDULO DE COMPRAS (app: purchases)
#   1) PROVEEDOR — alta / edición de ficha de proveedor
#   2) COMPRA    — cabecera de la compra (proveedor, fecha)
#   3) LÍNEAS    — formset de productos de la compra
# ============================================================
from django import forms
from django.forms import inlineformset_factory

from applications.product.models import Producto

from .models import Compra, CompraItem, Proveedor


# ============================================================
# 1) FORMULARIO DE PROVEEDOR
# ============================================================
class ProveedorForm(forms.ModelForm):
    class Meta:
        model = Proveedor
        fields = (
            'nombre', 'nit', 'contacto', 'telefono', 'email',
            'direccion', 'dias_entrega', 'activo', 'notas',
        )
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'k-form-input', 'placeholder': 'Nombre comercial'}),
            'nit': forms.TextInput(attrs={'class': 'k-form-input', 'placeholder': 'J05010012345678'}),
            'contacto': forms.TextInput(attrs={'class': 'k-form-input', 'placeholder': 'Persona de contacto'}),
            'telefono': forms.TextInput(attrs={'class': 'k-form-input', 'placeholder': '2222-3333'}),
            'email': forms.EmailInput(attrs={'class': 'k-form-input', 'placeholder': 'pedidos@proveedor.com'}),
            'direccion': forms.Textarea(attrs={'class': 'k-form-input', 'rows': 2, 'placeholder': 'Dirección de entrega'}),
            'dias_entrega': forms.TextInput(attrs={'class': 'k-form-input', 'placeholder': 'Ej: lunes y jueves'}),
            'activo': forms.CheckboxInput(attrs={'class': 'k-form-check'}),
            'notas': forms.Textarea(attrs={'class': 'k-form-input', 'rows': 3, 'placeholder': 'Condiciones, horarios, etc.'}),
        }


# ============================================================
# 2) FORMULARIO DE CABECERA DE COMPRA (proveedor + fecha)
# ============================================================
class CompraForm(forms.ModelForm):
    class Meta:
        model = Compra
        fields = ('proveedor', 'fecha', 'notas')
        widgets = {
            'proveedor': forms.Select(attrs={'class': 'k-form-input'}),
            'fecha': forms.DateInput(attrs={'class': 'k-form-input', 'type': 'date'}),
            'notas': forms.Textarea(attrs={'class': 'k-form-input', 'rows': 2,
                                            'placeholder': 'Referencia del pedido, nº de factura...'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Sólo proveedores activos aparecen en el desplegable
        self.fields['proveedor'].queryset = Proveedor.objects.filter(activo=True).order_by('nombre')
        self.fields['proveedor'].empty_label = "— Seleccionar proveedor —"


# ============================================================
# 3) LÍNEAS DE LA COMPRA (tabla de productos)
#    producto | cantidad | precio de compra (sin IVA) | % IVA
# ============================================================
class CompraItemForm(forms.ModelForm):
    class Meta:
        model = CompraItem
        fields = ('producto', 'cantidad', 'precio_unitario', 'porcentaje_iva')
        widgets = {
            'producto': forms.Select(attrs={'class': 'k-form-input'}),
            'cantidad': forms.NumberInput(attrs={'class': 'k-form-input', 'min': '1', 'placeholder': '0'}),
            'precio_unitario': forms.NumberInput(attrs={'class': 'k-form-input', 'step': '0.01',
                                                         'min': '0', 'placeholder': '0.00'}),
            'porcentaje_iva': forms.NumberInput(attrs={'class': 'k-form-input', 'step': '0.01',
                                                        'min': '0', 'max': '100', 'placeholder': 'auto'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['producto'].queryset = Producto.objects.filter(activo=True).order_by('nombre')
        self.fields['producto'].empty_label = "— Seleccionar producto —"
        self.fields['porcentaje_iva'].required = False
        self.fields['porcentaje_iva'].label = "% IVA (vacío = el del producto)"


CompraItemFormSet = inlineformset_factory(
    Compra,
    CompraItem,
    form=CompraItemForm,
    extra=3,             # filas vacías iniciales; se añaden más con el botón
    can_delete=False,
    # NOTA: sin min_num. Si fuera 1, Django NO marcaría la fila 0 como
    # "vacío permitido" y una compra sin líneas daría "This field is required"
    # en lugar de llegar a nuestro mensaje "Añade al menos un producto a la
    # compra." (que comprueba la vista CompraCreateView.post).
)
