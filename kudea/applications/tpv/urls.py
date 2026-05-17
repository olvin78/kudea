from django.contrib import admin
from . import views
from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from .views import (
    TpvIndexView, 
    TpvMesasView, 
    TpvCobrosView, 
    TpvHistorialView, 
    TpvConfigView,
    MesaCreateView, 
    MesaDetailView, 
    MesaUpdateView, 
    MesaDeleteView,
    ToggleMesaEstadoView,
    ComandaListView,
    ComandaCreateView,  # Asegúrate de que esta vista esté aquí
    ComandaDetailView,
    ComandaCerrarView,
    AgregarProductoACamadaView,
    ProductFilterView,
    EmpleadoListView,
    EmpleadoUpdateView,
    ProductListView, ProductCreateView, ProductUpdateView, ProductDeleteView, EmpleadoCreateView, MesaCategoriasView, MesaProductosPorCategoriaView, MesaComandaActivaRedirectView
)



app_name = 'tpv_app'

urlpatterns = [
    path('', TpvIndexView.as_view(), name='tpv_index'),

    # --- COMANDAS ---
    path('comandas/', ComandaListView.as_view(), name='tpv_comandas'),
    path('comandas_nueva/', ComandaCreateView.as_view(), name='create_comanda'),
    path('comandas/<int:pk>/', ComandaDetailView.as_view(), name='comanda_detail'),
    path('comandas/<int:pk>/cerrar/', ComandaCerrarView.as_view(), name='comanda_cerrar'),
    path('comandas/<int:comanda_id>/agregar-producto/', AgregarProductoACamadaView.as_view(), name='agregar_producto'),

    # --- PRODUCTOS ---
    path('productos/', ProductListView.as_view(), name='product_list'),
    path('productos/nuevo/', ProductCreateView.as_view(), name='product_create'),
    path('productos/editar/<int:pk>/', ProductUpdateView.as_view(), name='product_update'),
    path('productos/borrar/<int:pk>/', ProductDeleteView.as_view(), name='product_delete'),
    path('productos/<str:category>/', ProductFilterView.as_view(), name='filter_products'),

    # --- MESAS ---
    path('mesas/', TpvMesasView.as_view(), name='tpv_mesas'),
    path('mesa_create/', MesaCreateView.as_view(), name='mesa_create'),
    path('mesas/categoria/<int:pk>/', MesaDetailView.as_view(), name='mesa_categorias'),
    path('mesas/<int:mesa_id>/categorias/', MesaCategoriasView.as_view(), name='mesa_categorias'),
    path('mesas/<int:mesa_id>/categoria/<int:categoria_id>/productos/', MesaProductosPorCategoriaView.as_view(), name='mesa_productos'),
    path('mesas/<int:pk>/editar/', MesaUpdateView.as_view(), name='mesa_update'),
    path('mesas/<int:pk>/eliminar/', MesaDeleteView.as_view(), name='mesa_delete'),
    path('mesas/<int:pk>/toggle/', ToggleMesaEstadoView.as_view(), name='mesa_toggle_estado'),
    path('mesas/<int:mesa_id>/comanda-activa/', MesaComandaActivaRedirectView.as_view(), name='mesa_comanda_redirect'),

    # --- OTROS ---
    path('cobros/', TpvCobrosView.as_view(), name='tpv_cobros'),
    path('historial/', TpvHistorialView.as_view(), name='tpv_historial'),
    path('config/', TpvConfigView.as_view(), name='tpv_config'),

    # --- EMPLEADOS ---
    path('empleados_nuevo/', EmpleadoCreateView.as_view(), name='empleado_create'),
    path('empleados/', EmpleadoListView.as_view(), name='empleados_lista'),
    path('empleados/<int:pk>/editar/', EmpleadoUpdateView.as_view(), name='editar_empleado'),

] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
