from django.urls import path
from django.conf import settings
from django.conf.urls.static import static

from . import views, api_mentor
from .views import CrearCategoriaAjaxView, KudeaLandingPageView

app_name = 'home_app'

urlpatterns = [

    # ===========================
    # PRINCIPAL / LANDING
    # ===========================
    path('', KudeaLandingPageView.as_view(), name='kudea_landing'),
    path('home', views.HomePageView.as_view(), name='home'),

    # ===========================
    # TPV
    # ===========================
    path('home/Tpv_general', views.TpvGeneralView.as_view(), name='tpv_general'),
    path('kudea/', views.TPVView.as_view(), name='tpv'),
    path('home/procesar-venta/', views.ProcesarVentaView.as_view(), name='procesar_venta'),

    # ===========================
    # PRODUCTOS
    # ===========================
    path('home/productos/', views.ProductoListView.as_view(), name='lista_productos'),
    path('home/productos/crear/', views.CrearProductoView.as_view(), name='crear_producto'),
    path('categoria/ajax/crear/', CrearCategoriaAjaxView.as_view(), name='crear_categoria_ajax'),

    # ===========================
    # VENTAS / HISTORIAL
    # ===========================

    # Vista antigua (NO eliminada)
    path('home/ventas-old/', views.VentasListView.as_view(), name='lista_ventas_old'),

    # Nueva vista con filtros
    path('home/ventas/', views.HistorialVentasView.as_view(), name='lista_ventas'),

    # Detalle de venta
    path('home/venta/<int:pk>/', views.VentaDetalleView.as_view(), name='venta_detalle'),
    path('home/venta/<int:pk>/imprimir-pos/', views.imprimir_ticket_pos, name='imprimir_ticket_pos'),


    # ===========================
    # ARQUEOS
    # ===========================

    # Menú principal
    path('home/arqueo/', views.ArqueoMenuView.as_view(), name='arqueo_menu'),

    # Arqueos predefinidos
    path('home/arqueo/diario/', views.ArqueoDiarioView.as_view(), name='arqueo_diario'),
    path('home/arqueo/semanal/', views.ArqueoSemanalView.as_view(), name='arqueo_semanal'),
    path('home/arqueo/mensual/', views.ArqueoMensualView.as_view(), name='arqueo_mensual'),
    path('home/arqueo/anual/', views.ArqueoAnualView.as_view(), name='arqueo_anual'),

    # Arqueo personalizado
    path('home/arqueo/personalizado/', views.ArqueoPersonalizadoView.as_view(), name='arqueo_personalizado'),

    # Resultado del arqueo personalizado (POST)
    path('home/arqueo/personalizado/resultado/', views.ArqueoPersonalizadoView.as_view(),
         name='arqueo_personalizado_resultado'),

    # Exportar PDF (HTML por ahora)
    path('home/arqueo/pdf/<str:tipo>/', views.ArqueoPDFView.as_view(), name='arqueo_pdf'),


    # ===========================
    # APIs
    # ===========================
    path('home/api/productos/', views.obtener_productos, name='obtener_productos'),
    path('home/api/reporte-ventas/', views.reporte_ventas, name='reporte_ventas'),
    path('home/api/guardar-venta/', views.guardar_venta, name='guardar_venta'),
    # ===========================
    path("api/mentor/", api_mentor.mentor_query, name="mentor_api"),
    
    # COMUNICACIONES
    path('home/comunicaciones/leer/', views.mark_comms_read, name='mark_comms_read'),
    path('home/comunicaciones/crear/', views.create_comm, name='create_comm'),

    # AYUDA / SOPORTE
    # ===========================
    path("ayuda/", views.HelpCenterView.as_view(), name="ayuda"),
    path("acerca/", views.AboutVersionView.as_view(), name="acerca_version"),
    path("home/docs/sistema/", views.SistemaDocsView.as_view(), name="sistema_docs"),
]

# Servir archivos media en desarrollo
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
