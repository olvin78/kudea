from django.urls import path
from .views import PaymentMethodsView, DeletePaymentMethodView, UpdatePaymentMethodView

app_name = 'payments_app'

urlpatterns = [
    path('metodos/', PaymentMethodsView.as_view(), name='payment_methods'),
    path('metodos/<int:pk>/eliminar/', DeletePaymentMethodView.as_view(), name='delete_payment_method'),
    path('metodos/<int:pk>/editar/', UpdatePaymentMethodView.as_view(), name='update_payment_method'),
]
