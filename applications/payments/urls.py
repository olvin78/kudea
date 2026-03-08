from django.urls import path
from .views import PaymentMethodsView, DeletePaymentMethodView

app_name = 'payments_app'

urlpatterns = [
    path('metodos/', PaymentMethodsView.as_view(), name='payment_methods'),
    path('metodos/<int:pk>/eliminar/', DeletePaymentMethodView.as_view(), name='delete_payment_method'),
]
