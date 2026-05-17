from django.urls import path
from . import views

app_name = 'tpv_shop'


urlpatterns = [
    # Vistas principales
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



    # urls.py
    path('carrito/eliminar/<int:item_id>/', views.RemoveFromCartView.as_view(), name='remove_from_cart'),
    
    # Checkout
    path('checkout/', views.CheckoutView.as_view(), name='checkout'),
    path('recibo/', views.ReceiptSelectionView.as_view(), name='receipt_selection'),
    path('recibo/enviado/', views.EmailFormView.as_view(), name='receipt_sent'),
    
    path('tickets_list/', views.TicketListView.as_view(), name='ticket_list'),
    path('tickets/<int:pk>/', views.TicketDetailView.as_view(), name='ticket_detalle'),
    path('carrito/finalizar/', views.finalizar_compra, name='finalizar_compra'),
    


]