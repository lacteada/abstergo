"""Settings del Sistema Municipal de Gestión de Atención Ciudadana.

Toda la configuración sale del archivo .env. Ver .env.example.
"""

import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent

load_dotenv(BASE_DIR / ".env")


def env(nombre, default=""):
    return os.environ.get(nombre, default)


def env_bool(nombre, default=False):
    return env(nombre, str(default)).strip().lower() in ("1", "true", "yes", "si")


def env_list(nombre, default=""):
    return [valor.strip() for valor in env(nombre, default).split(",") if valor.strip()]


SECRET_KEY = env("SECRET_KEY")
DEBUG = env_bool("DEBUG", True)
ALLOWED_HOSTS = env_list("ALLOWED_HOSTS", "localhost,127.0.0.1")


INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "apps.organizacion",
    "apps.cuentas",
    "apps.catalogos",
    "apps.ciudadanos",
    "apps.atenciones",
    "apps.cumplimiento",
    "apps.panel",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"


DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.mysql",
        "NAME": env("DB_NAME"),
        "USER": env("DB_USER"),
        "PASSWORD": env("DB_PASSWORD"),
        "HOST": env("DB_HOST", "127.0.0.1"),
        "PORT": env("DB_PORT", "3306"),
        "OPTIONS": {
            "charset": "utf8mb4",
            "init_command": "SET sql_mode='STRICT_TRANS_TABLES'",
        },
    }
}


# Usuario propio: sin username, con el correo como campo de acceso.
AUTH_USER_MODEL = "cuentas.Usuario"


AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
        "OPTIONS": {"min_length": int(env("PASSWORD_MIN_LENGTH", "8"))},
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
    {
        "NAME": "apps.cuentas.validators.RequisitosInstitucionalesValidator",
    },
]


LANGUAGE_CODE = env("LANGUAGE_CODE", "es")
TIME_ZONE = env("TIME_ZONE", "America/Santiago")
USE_I18N = True
USE_TZ = True


STATIC_URL = "static/"
STATICFILES_DIRS = [BASE_DIR / "static"]
STATIC_ROOT = BASE_DIR / "staticfiles"


# MAILERS reemplaza a EMAIL_BACKEND desde Django 6.0. Las OPTIONS se pasan
# como argumentos al backend, y cada backend rechaza las que no conoce, así
# que solo se declaran cuando el backend es el de SMTP.
MAILER_BACKEND = env("MAILER_BACKEND", "django.core.mail.backends.console.EmailBackend")

MAILERS = {"default": {"BACKEND": MAILER_BACKEND}}

if MAILER_BACKEND == "django.core.mail.backends.smtp.EmailBackend":
    MAILERS["default"]["OPTIONS"] = {
        "host": env("EMAIL_HOST"),
        "port": int(env("EMAIL_PORT", "587")),
        "username": env("EMAIL_HOST_USER"),
        "password": env("EMAIL_HOST_PASSWORD"),
        "use_tls": env_bool("EMAIL_USE_TLS", True),
    }

DEFAULT_FROM_EMAIL = env("DEFAULT_FROM_EMAIL", "no-reply@muniserena.cl")


# Login y logout del sistema. La app cuentas sirve la pantalla; el Admin
# conserva el suyo, aparte.
LOGIN_URL = "cuentas:login"
LOGIN_REDIRECT_URL = "panel:inicio"
LOGOUT_REDIRECT_URL = "cuentas:login"


# Validez del código OTP, en minutos (mockup §3).
OTP_EXPIRY_MINUTES = int(env("OTP_EXPIRY_MINUTES", "10"))

# Contraseña inicial que el comando cargar_datos asigna a los usuarios migrados.
USUARIOS_PASSWORD_INICIAL = env("USUARIOS_PASSWORD_INICIAL")
