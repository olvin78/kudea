# applications/accounts/urls.py
from django.urls import path
from .views import AccountsListView  # Asegúrate de tener esta vista

app_name = 'accounts_app'

urlpatterns = [
    path('', AccountsListView.as_view(), name='accounts_list'),
]
