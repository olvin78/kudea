# Usamos una imagen oficial y ligera de Python
FROM python:3.11-slim

# Variables de entorno para Python y Django
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DJANGO_SETTINGS_MODULE=kudea.settings

# Definimos el directorio de trabajo dentro del contenedor
WORKDIR /app

# Instalamos dependencias del sistema operativo (necesarias para compilar librerías de Python si hace falta)
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        gcc \
        libpq-dev \
        libpango-1.0-0 \
        libpangoft2-1.0-0 \
        libgdk-pixbuf-2.0-0 \
        libffi-dev \
        shared-mime-info \
    && rm -rf /var/lib/apt/lists/*

# Copiamos solo el requirements.txt primero, para aprovechar la caché de Docker
# si el requirements no cambia, no volverá a descargar todos los paquetes
COPY requirements.txt /app/

# Instalamos las librerías de Python listadas en requirements.txt
RUN pip install --upgrade pip \
    && pip install -r requirements.txt

# Copiamos todo el código de nuestra aplicación a la carpeta /app del contenedor
COPY . /app/

# Exponemos el puerto 8000 para que podamos acceder a la web desde nuestro navegador
EXPOSE 8000

# Añadimos un script para iniciar la aplicación (migraciones y servidor)
# Esto garantiza que al reiniciar el contenedor en otro ordenador, primero prepare la BBDD.
CMD ["bash", "-c", "python manage.py makemigrations && python manage.py migrate && python manage.py runserver 0.0.0.0:8000"]
