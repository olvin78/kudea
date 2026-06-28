import io
import os
import re
import tempfile
import shutil
import urllib.parse
from pathlib import Path

from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand
from django.utils.text import slugify

from applications.product.models import Producto

from bing_image_downloader import downloader


CLEAN_QUERY = re.compile(r"\(.*?\)")


def clean_name(name):
    name = CLEAN_QUERY.sub("", name).strip()
    replacements = {
        "grande": "",
        "pequeño": "",
        "pequeno": "",
        "en bolsa": "",
        "en bolsas": "",
        "en botella": "",
        "12 onzas": "",
    }
    for old, new in replacements.items():
        name = name.lower().replace(old, new)
    name = re.sub(r"\s+", " ", name).strip()
    return name


class Command(BaseCommand):
    help = "Busca imágenes en Bing para productos sin imagen"

    def add_arguments(self, parser):
        parser.add_argument("--max", type=int, default=0)

    def handle(self, *args, **options):
        sin_imagen = Producto.objects.filter(imagen="")
        total = sin_imagen.count()
        max_prod = options["max"]
        if max_prod and max_prod < total:
            sin_imagen = list(sin_imagen)[:max_prod]
        else:
            sin_imagen = list(sin_imagen)

        self.stdout.write(f"Buscando imágenes para {len(sin_imagen)} productos...")

        ok = 0
        errors = 0

        for producto in sin_imagen:
            query = clean_name(producto.nombre)
            if not query:
                query = producto.nombre
            search_query = f"{query} producto"

            self.stdout.write(f"  [{producto.id}] '{producto.nombre}' -> buscando '{search_query}'...", ending="")

            tmpdir = tempfile.mkdtemp()
            try:
                downloader.download(
                    search_query,
                    limit=1,
                    output_dir=tmpdir,
                    adult_filter_off=False,
                    force_replace=False,
                    timeout=10,
                )
                downloaded = []
                for root, dirs, files in os.walk(tmpdir):
                    for f in files:
                        if f.lower().endswith((".jpg", ".jpeg", ".png", ".webp", ".gif")):
                            downloaded.append(os.path.join(root, f))

                if not downloaded:
                    self.stdout.write(self.style.WARNING(" sin resultados"))
                    continue

                img_path = downloaded[0]
                with open(img_path, "rb") as f:
                    content = f.read()

                slug = slugify(producto.nombre)[:50]
                ext = Path(img_path).suffix or ".jpg"
                filename = f"{slug}{ext}"

                producto.imagen.save(filename, ContentFile(content), save=False)
                producto.save()
                ok += 1
                self.stdout.write(self.style.SUCCESS(" OK"))
            except Exception as e:
                errors += 1
                self.stdout.write(self.style.ERROR(f" ERROR: {e}"))
            finally:
                shutil.rmtree(tmpdir, ignore_errors=True)

        pendientes = Producto.objects.filter(imagen="").count()
        self.stdout.write(
            self.style.SUCCESS(
                f"\nCompletado: {ok} imágenes agregadas, {errors} errores, {pendientes} pendientes"
            )
        )
