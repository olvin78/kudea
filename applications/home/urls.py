from django.urls import path
from . import views  # Asegúrate de importar views correctamente


app_name = 'home_app'


urlpatterns = [
    path('', views.HomePageView.as_view(), name='home'),  # Página de inicio

]
