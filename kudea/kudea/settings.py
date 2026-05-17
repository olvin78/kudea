
from pathlib import Path
import os

BASE_DIR = Path(__file__).resolve().parent.parent


def get_env_int(name, default):
    value = os.environ.get(name, str(default))
    try:
        return int(value)
    except (TypeError, ValueError):
        return default

# Seguridad de Entorno (Environment Variables)
# Estas variables deben inyectarse en el servidor o archivo .env manejado externamente
SECRET_KEY = os.environ.get('DJANGO_SECRET_KEY', 'django-insecure-n=h4#+90b^n2xw!i@$gn935an+5pulpw9isidot+q7fr!gvc@4')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.environ.get('DJANGO_DEBUG', 'True') == 'True'

ALLOWED_HOSTS = (os.environ.get('DJANGO_ALLOWED_HOSTS') or '*').split(',')

CSRF_TRUSTED_ORIGINS = [
    "https://*.loca.lt",
]

# Añadir dominios dinámicos si existen en variables de entorno
if os.environ.get('DJANGO_CSRF_TRUSTED'):
    CSRF_TRUSTED_ORIGINS.extend(os.environ.get('DJANGO_CSRF_TRUSTED').split(','))

# Application definition

INSTALLED_APPS = [
    'applications.product',
    'applications.home',
    'applications.tpv',
    'applications.support',
    'applications.budget',
    'applications.tpv_shop',
    'applications.customer',  # ← esto debe estar exactamente así
    'applications.attendance',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    'widget_tweaks',

    'applications.invoice',
    'applications.cash',
    'applications.stock',
    'applications.reporting',
    'applications.cashflow',
    'applications.payments',
    'applications.accounts',
    'applications.recordlog',
    'applications.employee',
    'applications.config',

    # Django Sites
    'django.contrib.sites',

    # Allauth
    'allauth',
    'allauth.account',
    'allauth.socialaccount',
    'allauth.socialaccount.providers.google',
    'django_cotton',
]

SITE_ID = get_env_int("DJANGO_SITE_ID", 3)

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',

    # Allauth middleware
    'allauth.account.middleware.AccountMiddleware',

    'applications.home.middleware.ModuloActivoMiddleware',
]

ROOT_URLCONF = 'kudea.urls'

# settings.py
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [
            BASE_DIR / 'templates',
        ],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'applications.home.context_processors.modulos_activos',
                'applications.home.context_processors.comunicaciones_context',
            ],
        },
    },
]

WSGI_APPLICATION = 'kudea.wsgi.application'
TEST_RUNNER = 'kudea.test_runner.ProjectDiscoverRunner'


# Database
# https://docs.djangoproject.com/en/5.1/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}


# Password validation
# https://docs.djangoproject.com/en/5.1/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# Authentication Backends
AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',
    'allauth.account.auth_backends.AuthenticationBackend',
]

# Allauth Settings
ACCOUNT_LOGOUT_ON_GET = True
ACCOUNT_LOGIN_METHODS = {'email'}
ACCOUNT_EMAIL_REQUIRED = True
ACCOUNT_EMAIL_VERIFICATION = 'none'
LOGIN_URL = '/accounts/login/'
LOGIN_REDIRECT_URL = '/'
LOGOUT_REDIRECT_URL = '/'
SOCIALACCOUNT_LOGIN_ON_GET = True
SOCIALACCOUNT_ADAPTER = 'allauth.socialaccount.adapter.DefaultSocialAccountAdapter'


# Google Provider Settings
SOCIALACCOUNT_PROVIDERS = {
    'google': {
        'SCOPE': [
            'profile',
            'email',
        ],
        'AUTH_PARAMS': {
            'access_type': 'online',
        }
    }
}


# Internationalization
# https://docs.djangoproject.com/en/5.1/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'Europe/Madrid'

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.1/howto/static-files/

# settings.py
STATIC_URL = '/static/'

STATICFILES_DIRS = [
    BASE_DIR / "static",  # Si usas Pathlib
]

# Configuración para archivos de medios (imágenes, etc.)
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# Directorio donde se guardarán los archivos subidos (en tu máquina local)
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# URL base para acceder a los archivos subidos
MEDIA_URL = '/media/'


# Default primary key field type
# https://docs.djangoproject.com/en/5.1/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'


# settings.py

EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'  # O el servicio que estés usando
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'tu_correo@example.com'  # Tu correo electrónico
EMAIL_HOST_PASSWORD = 'tu_contraseña'  # Tu contraseña de correo
DEFAULT_FROM_EMAIL = 'no-reply@example.com'  # El correo de salida
