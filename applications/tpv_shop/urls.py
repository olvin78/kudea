from django.urls import path
from . import views
from .views import FinalizarCompraView, EliminarTicketView, CajaArqueoCreateView, CajaArqueoListView, CajaArqueoDetailView, CajaArqueoDeleteView, ArqueoAutomaticoView

app_name = 'tpv_shop'


urlpatterns = [
    # Vistas principaless
    path('', views.TpvShopIndexView.as_view(), name='index'),
    path('productos/', views.ProductListView.as_view(), name='product_list'),
    path('productos/<slug:category_slug>/', views.ProductListView.as_view(), name='product_list_by_category'),
    path('producto/<slug:slug>/', views.ProductDetailView.as_view(), name='product_detail'),
    
    # Categorías
    path('categorias/', views.CategoryListView.as_view(), name='category_list'),
    path('categoria/<slug:slug>/', views.CategoryDetailView.as_view(), name='category_detail'),
    
    # Servicios
    path('servicios/', views.ServiceListView.as_view(), name='service_list'),
    path('servicio/<slug:slug>/', views.ServiceDetailView.as_view(), name='service_detail'),
    
    # Carrito
    path('carrito/', views.CartView.as_view(), name='cart'),
    path('carrito/agregar/<int:product_id>/', views.AddToCartView.as_view(), name='add_to_cart'),
    path('carrito/actualizar/', views.UpdateCartView.as_view(), name='update_cart'),
    path('carrito/actualizar/ajax/', views.UpdateCartAjaxView.as_view(), name='update_cart_ajax'),
    
    path('carrito/finalizar/', FinalizarCompraView.as_view(), name='finalizar_compra'),



    # urls.py
    path('carrito/eliminar/<int:item_id>/', views.RemoveFromCartView.as_view(), name='remove_from_cart'),
    
    # Checkout
    path('checkout/', views.CheckoutView.as_view(), name='checkout'),
    path('recibo/', views.ReceiptSelectionView.as_view(), name='receipt_selection'),
    path('recibo/enviado/', views.EmailFormView.as_view(), name='receipt_sent'),
    
    path('tickets_list/', views.TicketListView.as_view(), name='ticket_list'),
    path('tickets/<int:pk>/', views.TicketDetailView.as_view(), name='ticket_detalle'),
    path('ticket/<int:pk>/eliminar/', EliminarTicketView.as_view(), name='eliminar_ticket'),

    # Estás poniendo esto en urls.py:
    path('api/tickets-del-dia/', views.tickets_del_dia, name='tickets_del_dia'),


    path('arqueo_caja/', CajaArqueoCreateView.as_view(), name='caja_arqueo_create'),
    path('arqueo_lista/', CajaArqueoListView.as_view(), name='caja_arqueo_list'),
    path('arqueo/<int:pk>/', CajaArqueoDetailView.as_view(), name='caja_arqueo_detail'),
    path('arqueo/<int:pk>/eliminar/', CajaArqueoDeleteView.as_view(), name='caja_arqueo_delete'),
    path('arqueo-automatico/', views.ArqueoAutomaticoView.as_view(), name='arqueo_automatico'),  # Ruta de Arqueo Automático
    path('api/guardar-arqueo-auto/', views.guardar_arqueo_auto, name='guardar_arqueo_auto'),


]