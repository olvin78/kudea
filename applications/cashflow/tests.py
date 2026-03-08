from django.test import TestCase

# Create your tests here.
from django.urls import path
from .views import CashflowListView

app_name = "cashflow"

urlpatterns = [
    path("", CashflowListView.as_view(), name="list"),
]