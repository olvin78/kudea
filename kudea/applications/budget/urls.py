from django.urls import path
from . import views

app_name = "budget_app"  # ✅ Aquí es donde va

urlpatterns = [
    path('', views.BudgetMainView.as_view(), name='budget_main'),
    path('budget/<int:pk>/', views.BudgetDetailView.as_view(), name='budget_detail'),
    path('add-client/', views.add_client, name='add_client'),
    path('delete-item/<int:item_id>/', views.delete_budget_item, name='delete_item'),
    path('budget/update/<int:pk>/', views.BudgetUpdateView.as_view(), name='update_budget'),
    path('list/', views.BudgetListView.as_view(), name='budget_list'),  # 👈 importante
    path('budget/create/', views.BudgetCreateView.as_view(), name='budget_create'),
    
]
