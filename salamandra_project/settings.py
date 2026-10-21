"""
Configuración de Django para SalaMandra.

Base de datos: SQLite, usando el ORM de Django. Los modelos están en
reservas/models.py y reproducen el diagrama entidad-relación del equipo.

Apps instaladas: se dejaron solo las necesarias a propósito. No se incluyen
django.contrib.admin / auth / contenttypes / sessions, para que la base de
datos contenga ÚNICAMENTE las tablas del equipo (más django_migrations, que
Django usa para llevar el control de las migraciones). El login de
Administrador se implementó a mano sobre las tablas `usuarios` y `roles`
(ver cuentas/services.py y cuentas/views.py), y la sesión se guarda en
una cookie firmada (ver SESSION_ENGINE más abajo).
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
INSTALLED_APPS = [
    "django.contrib.staticfiles",
    "django.contrib.messages",
    "reservas",
    "cuentas",
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

# --- Base de datos: SQLite -----------------------------------------------------
# SQLite guarda todo en un único archivo (db.sqlite3, en la raíz del proyecto).
# No hay servicio que instalar ni usuario/contraseña: Django lo crea solo al
# ejecutar `python manage.py migrate`.
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}

# --- Sesiones -----------------------------------------------------------------
# La sesión se guarda firmada en una cookie, así no hace falta la tabla
# django_session (la base de datos queda solo con las tablas del equipo).
SESSION_ENGINE = "django.contrib.sessions.backends.signed_cookies"
SESSION_COOKIE_AGE = 60 * 60 * 4  # 4 horas

LOGIN_URL = "login"

# --- Validación de contraseñas -----------------------------------------------
AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
        "OPTIONS": {"min_length": 8},
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]

# --- Internacionalización ---------------------------------------------------
LANGUAGE_CODE = "es"
TIME_ZONE = "America/La_Paz"
USE_I18N = True
USE_TZ = True

# --- Archivos estáticos ------------------------------------------------------
STATIC_URL = "static/"

DEFAULT_AUTO_FIELD = "django.db.models.AutoField"

# Fechas del calendario universitario, en formato YYYY-MM-DD.
# Completar con los feriados confirmados por la universidad.
RESERVAS_FERIADOS = []
