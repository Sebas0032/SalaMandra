"""
Configuración de Django para SalaMandra.

IMPORTANTE — decisión de arquitectura (Sesión 07):
Este proyecto usa MongoDB como base de datos y accede a ella directamente
con `pymongo` (ver reservas/mongo.py y reservas/services.py). NO se usa el
ORM de Django (django.db.models) ni una base de datos relacional.

Por eso:
- DATABASES queda vacío a propósito. No ejecuten `python manage.py migrate`:
  no hay nada que migrar y el comando fallará porque no hay una base de
  datos relacional configurada (eso es esperado, no es un error del código).
- No están instaladas las apps django.contrib.auth / contenttypes / admin,
  porque esas apps dependen del ORM de Django. El login de Administrador
  se implementó a mano en reservas/views.py usando sesiones de Django
  (ver SESSION_ENGINE más abajo) y las credenciales guardadas en MongoDB.
"""

import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

# --- Seguridad básica (desarrollo) ---------------------------------------
SECRET_KEY = os.environ.get(
    "DJANGO_SECRET_KEY",
    "clave-de-desarrollo-salamandra-no-usar-en-produccion",
)

DEBUG = True

ALLOWED_HOSTS = ["*"]

# --- Apps instaladas -------------------------------------------------------
# Deliberadamente NO incluimos:
#   - django.contrib.admin        (requiere el ORM)
#   - django.contrib.auth         (requiere el ORM para el modelo User)
#   - django.contrib.contenttypes (lo usa el admin/auth)
INSTALLED_APPS = [
    "django.contrib.staticfiles",
    "django.contrib.sessions",
    "django.contrib.messages",
    "reservas",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "salamandra_project.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "salamandra_project.wsgi.application"

# --- Base de datos relacional: NO SE USA ------------------------------------
# Ver nota al inicio del archivo. Se deja vacío intencionalmente.
DATABASES = {}

# --- Sesiones sin base de datos relacional ----------------------------------
# Guarda la sesión firmada en una cookie en vez de en una tabla de BD,
# para poder tener "login de Administrador" sin usar el ORM de Django.
SESSION_ENGINE = "django.contrib.sessions.backends.signed_cookies"
SESSION_COOKIE_AGE = 60 * 60 * 4  # 4 horas

LOGIN_URL = "login"

# --- Internacionalización ---------------------------------------------------
LANGUAGE_CODE = "es"
TIME_ZONE = "America/La_Paz"
USE_I18N = True
USE_TZ = True

# --- Archivos estáticos ------------------------------------------------------
STATIC_URL = "static/"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# --- Conexión a MongoDB (pymongo) -------------------------------------------
# Pueden sobreescribir estos valores con variables de entorno, por ejemplo
# si usan MongoDB Atlas en vez de un MongoDB local. Ver README.md.
MONGO_URI = os.environ.get("MONGO_URI", "mongodb://localhost:27017/")
MONGO_DB_NAME = os.environ.get("MONGO_DB_NAME", "salamandra_db")
