import requests
import io
import urllib.parse
from pathlib import Path

from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand
from django.utils.text import slugify

from applications.product.models import Categoria, Producto
from decimal import Decimal


API_URL = "https://fakestoreapi.com/products"
CATEGORY_MAP = {
    "electronics": "Electrónica",
    "jewelery": "Joyería",
    "men's clothing": "Ropa Hombre",
    "women's clothing": "Ropa Mujer",
}

STOCK_BY_CATEGORY = {
    "Electrónica": 15,
    "Joyería": 25,
    "Ropa Hombre": 50,
    "Ropa Mujer": 50,
}


class Command(BaseCommand):
    help = "Importa productos desde la Fake Store API con imágenes"

    def handle(self, *args, **options):
        self.stdout.write("Obteniendo productos de la API...")
        resp = requests.get(API_URL, timeout=30)
        resp.raise_for_status()
        products_data = resp.json()
        self.stdout.write(f"Recibidos {len(products_data)} productos")

        created_count = 0
        for item in products_data:
            api_category = item.get("category", "uncategorized")
            cat_name = CATEGORY_MAP.get(api_category, api_category.title())
            categoria, _ = Categoria.objects.get_or_create(
                nombre=cat_name,
                defaults={"slug": slugify(cat_name)},
            )

            nombre = item.get("title", "Sin nombre")
            precio = Decimal(str(item.get("price", 0)))
            imagen_url = item.get("image", "")

            slug_base = slugify(nombre)[:50]
            slug = slug_base
            counter = 1
            while Producto.objects.filter(slug=slug).exists():
                slug = f"{slug_base}-{counter}"
                counter += 1

            producto = Producto(
                nombre=nombre,
                slug=slug,
                categoria=categoria,
                precio=precio,
                stock=STOCK_BY_CATEGORY.get(cat_name, 10),
                stock_minimo=5,
                activo=True,
            )

            if imagen_url:
                try:
                    img_resp = requests.get(imagen_url, timeout=30)
                    img_resp.raise_for_status()
                    ext = Path(urllib.parse.urlparse(imagen_url).path).suffix or ".jpg"
                    filename = f"{slug}{ext}"
                    producto.imagen.save(
                        filename,
                        ContentFile(img_resp.content),
                        save=False,
                    )
                except Exception as e:
                    self.stdout.write(f"  Error descargando imagen para '{nombre}': {e}")

            producto.save()
            created_count += 1
            self.stdout.write(f"  [{created_count}] {nombre} - {precio}€ [{cat_name}]")

        self.stdout.write(self.style.SUCCESS(f"\n¡Importación completa! {created_count} productos creados."))
