import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'kudea.settings')
django.setup()

from applications.product.models import Producto, Categoria

# Categorías de demo
cat_bebidas, _ = Categoria.objects.get_or_create(nombre='Bebidas')
cat_comida, _ = Categoria.objects.get_or_create(nombre='Comida')
cat_postres, _ = Categoria.objects.get_or_create(nombre='Postres')
cat_elec, _ = Categoria.objects.get_or_create(nombre='Electrónica')
cat_ropa, _ = Categoria.objects.get_or_create(nombre='Ropa')

productos_demo = [
    {'nombre': 'Agua Mineral', 'precio': 1.20, 'stock': 100, 'categoria': cat_bebidas},
    {'nombre': 'Coca-Cola', 'precio': 1.80, 'stock': 80, 'categoria': cat_bebidas},
    {'nombre': 'Zumo de Naranja', 'precio': 2.50, 'stock': 50, 'categoria': cat_bebidas},
    {'nombre': 'Café Solo', 'precio': 1.50, 'stock': 200, 'categoria': cat_bebidas},
    {'nombre': 'Cerveza', 'precio': 2.80, 'stock': 60, 'categoria': cat_bebidas},
    {'nombre': 'Bocadillo Jamón', 'precio': 4.50, 'stock': 30, 'categoria': cat_comida},
    {'nombre': 'Pizza Margarita', 'precio': 8.90, 'stock': 20, 'categoria': cat_comida},
    {'nombre': 'Ensalada César', 'precio': 7.50, 'stock': 25, 'categoria': cat_comida},
    {'nombre': 'Hamburguesa Clásica', 'precio': 9.50, 'stock': 15, 'categoria': cat_comida},
    {'nombre': 'Tosta Aguacate', 'precio': 5.80, 'stock': 40, 'categoria': cat_comida},
    {'nombre': 'Brownie Chocolate', 'precio': 3.50, 'stock': 35, 'categoria': cat_postres},
    {'nombre': 'Tarta de Queso', 'precio': 4.20, 'stock': 20, 'categoria': cat_postres},
    {'nombre': 'Helado Vainilla', 'precio': 2.90, 'stock': 50, 'categoria': cat_postres},
    {'nombre': 'Cable USB-C', 'precio': 12.90, 'stock': 45, 'categoria': cat_elec},
    {'nombre': 'Auriculares Básico', 'precio': 19.99, 'stock': 30, 'categoria': cat_elec},
    {'nombre': 'Funda Móvil', 'precio': 8.50, 'stock': 60, 'categoria': cat_elec},
    {'nombre': 'Camiseta Blanca', 'precio': 14.99, 'stock': 100, 'categoria': cat_ropa},
    {'nombre': 'Sudadera Azul', 'precio': 29.99, 'stock': 40, 'categoria': cat_ropa},
    {'nombre': 'Calcetines Pack 3', 'precio': 6.50, 'stock': 80, 'categoria': cat_ropa},
]

created = 0
for p in productos_demo:
    obj, was_created = Producto.objects.get_or_create(nombre=p['nombre'], defaults={
        'precio': p['precio'],
        'stock': p['stock'],
        'categoria': p['categoria'],
        'activo': True,
    })
    if was_created:
        created += 1

print(f'✅ {created} productos nuevos creados.')
print(f'📦 Total productos en BD: {Producto.objects.count()}')
