#!/usr/bin/env bash
# Verificación reproducible de abstergo.
# Corre sobre un SQLite temporal fuera del repo: la máquina local no tiene MariaDB.
set -euo pipefail

cd "$(dirname "$0")/.."
RAIZ="$PWD"
SCRATCH="$(mktemp -d)"
trap 'rm -rf "$SCRATCH"' EXIT

cat > "$SCRATCH/settings_verif.py" <<'PY'
import os
from config.settings import *  # noqa: F401,F403
ALLOWED_HOSTS = ["testserver", "localhost", "127.0.0.1"]
DATABASES = {"default": {
    "ENGINE": "django.db.backends.sqlite3",
    "NAME": os.path.join(os.path.dirname(__file__), "verif.sqlite3"),
}}
PY

export DJANGO_SETTINGS_MODULE=settings_verif
export PYTHONPATH="$SCRATCH:$RAIZ"

# Un clon limpio (CI) no tiene .env, y sin SECRET_KEY la configuración revienta.
# La verificación aporta valores de prueba y manda el correo a la consola.
export SECRET_KEY="verificacion-sin-secreto"
export MAILER_BACKEND="django.core.mail.backends.console.EmailBackend"
export USUARIOS_PASSWORD_INICIAL="Clave.Verificacion1"

PY="$RAIZ/venv/bin/python"
[ -x "$PY" ] || PY="$(command -v python3)"

paso() { printf '\n== %s ==\n' "$1"; }

paso "check"
"$PY" manage.py check

paso "migraciones sin cambios pendientes"
"$PY" manage.py makemigrations --check --dry-run

paso "migrate"
"$PY" manage.py migrate --noinput

paso "carga de datos"
"$PY" manage.py cargar_datos

if "$PY" -m ruff --version >/dev/null 2>&1; then
  paso "ruff"
  "$PY" -m ruff check .
else
  paso "ruff (no instalado, se omite)"
fi

if "$PY" -c "import pytest" 2>/dev/null; then
  paso "pytest"
  "$PY" -m pytest -q
else
  paso "pytest (no instalado, se omite)"
fi

paso "smoke de rutas y de la API"
"$PY" - <<'PY'
import os, django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "settings_verif")
django.setup()
from django.test.utils import setup_test_environment
setup_test_environment()
from django.contrib.auth import get_user_model
from django.test import Client
from apps.cuentas.models import RecuperacionPassword, Rol

U = get_user_model()
u, _ = U.objects.get_or_create(email="admin@test.cl",
    defaults={"first_name": "A", "last_name": "B",
              "is_staff": True, "is_superuser": True})
u.set_password("Clave.123"); u.save()

c = Client()
c.post("/login/", {"username": "admin@test.cl", "password": "Clave.123"}, follow=True)
for ruta in ["/", "/delegaciones/", "/usuarios/", "/roles/", "/metas/",
             "/tipos-atencion/", "/sub-atenciones/", "/vecinos/",
             "/atenciones/", "/atenciones/crear/", "/admin/"]:
    assert c.get(ruta).status_code == 200, ruta

# API v1: esquema, login por token, y las rutas del contrato en inglés.
assert c.get("/api/schema/").status_code == 200, "schema"
esquema = c.get("/api/schema/").content.decode()
for ruta_api in ["/api/v1/auth/recover/", "/api/v1/auth/verify/",
                 "/api/v1/auth/new-password/", "/api/v1/auth/register/",
                 "/api/v1/neighbors/", "/api/v1/cases/"]:
    assert ruta_api in esquema, ruta_api

a = Client()
r = a.post("/api/v1/auth/login/", {"email": "admin@test.cl", "password": "Clave.123"})
assert r.status_code == 200, ("login api", r.status_code)
auth = {"HTTP_AUTHORIZATION": f"Bearer {r.json()['access']}"}
assert a.get("/api/v1/auth/me/", **auth).status_code == 200, "me"
assert a.get("/api/v1/neighbors/").status_code == 401, "neighbors sin token"
assert a.get("/api/v1/neighbors/", **auth).status_code == 200, "neighbors con token"

# El contrato está en inglés.
perfil = a.get("/api/v1/auth/me/", **auth).json()
assert perfil["role_code"] == "admin", perfil.get("role_code")
assert "users" in perfil["read_modules"], perfil.get("read_modules")
vecino = a.get("/api/v1/neighbors/", **auth).json()["results"][0]
assert set(vecino) >= {"name", "rut", "address", "phone", "territory",
                       "management_type", "status"}, sorted(vecino)

# Permisos por rol, con una cuenta de solo lectura.
rol, _ = Rol.objects.get_or_create(codigo="consulta", defaults={"nombre": "CONSULTA"})
u2, _ = U.objects.get_or_create(email="consulta@test.cl",
    defaults={"first_name": "C", "last_name": "D"})
u2.rol = rol; u2.set_password("Clave.123"); u2.is_active = True; u2.save()

b = Client()
rb = b.post("/api/v1/auth/login/", {"email": "consulta@test.cl", "password": "Clave.123"})
assert rb.status_code == 200, ("login consulta", rb.status_code)
authb = {"HTTP_AUTHORIZATION": f"Bearer {rb.json()['access']}"}
assert b.get("/api/v1/neighbors/", **authb).status_code == 200, "consulta lee"
assert b.post("/api/v1/neighbors/", {}, **authb).status_code == 403, "consulta no escribe"
assert b.get("/api/v1/users/", **authb).status_code == 403, "consulta no ve usuarios"
b.post("/login/", {"username": "consulta@test.cl", "password": "Clave.123"}, follow=True)
assert b.get("/usuarios/").status_code == 403, "web: usuarios prohibido"
assert b.get("/vecinos/").status_code == 200, "web: vecinos permitido"
perfil2 = b.get("/api/v1/auth/me/", **authb).json()
assert perfil2["role_code"] == "consulta", perfil2.get("role_code")
assert "users" not in perfil2["read_modules"]
assert "neighbors" in perfil2["read_modules"]
assert "neighbors" not in perfil2["write_modules"]

# Registro público: el correo es el identificador y no se puede repetir. El
# nombre y el apellido son obligatorios, y el correo se guarda en minúsculas.
alta = {"email": "Nuevo@Test.CL", "first_name": "Nuevo", "last_name": "Apellido",
        "password": "Clave.123"}
assert a.post("/api/v1/auth/register/", alta).status_code == 201, "registro"
nuevo = U.objects.get(email="nuevo@test.cl")
assert (nuevo.first_name, nuevo.last_name) == ("Nuevo", "Apellido"), "titular guardado"
assert a.post("/api/v1/auth/register/", alta).status_code == 400, "correo repetido"
assert a.post("/api/v1/auth/register/",
              {"email": "sin-titular@test.cl", "password": "Clave.123"}).status_code == 400, "sin titular"

# Recuperación de contraseña: bloquea la cuenta y la reactiva al guardarla.
a.post("/api/v1/auth/recover/", {"email": "admin@test.cl"})
u.refresh_from_db()
assert u.is_active is False, "la cuenta debía bloquearse al pedir recuperación"
assert a.post("/api/v1/auth/login/",
              {"email": "admin@test.cl", "password": "Clave.123"}).status_code == 401, "bloqueada"
rec = RecuperacionPassword.objects.filter(usuario=u).order_by("-creado").first()
assert rec is not None, "sin recuperación"
assert a.post("/api/v1/auth/verify/",
              {"email": "admin@test.cl", "code": rec.codigo}).status_code == 200, "verify"
assert a.post("/api/v1/auth/new-password/",
              {"email": "admin@test.cl", "code": rec.codigo,
               "password": "Nueva.Clave.123"}).status_code == 200, "nueva password"
u.refresh_from_db()
assert u.is_active is True, "la cuenta debía reactivarse"
assert a.post("/api/v1/auth/login/",
              {"email": "admin@test.cl", "password": "Nueva.Clave.123"}).status_code == 200, "login nuevo"
print("SMOKE OK")
PY

printf '\nVERIFICACIÓN OK\n'
