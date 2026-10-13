#!/usr/bin/env bash
# Verificación reproducible de abstergo.
# Corre sobre un SQLite temporal fuera del repo: la máquina local no tiene MariaDB.
# Es la fuente ejecutable del §5 de AGENTS.md.
set -euo pipefail

cd "$(dirname "$0")/.."
RAIZ="$PWD"
SCRATCH="$(mktemp -d)"
trap 'rm -rf "$SCRATCH"' EXIT

cat > "$SCRATCH/settings_verif.py" <<'PY'
import os
from config.settings import *  # noqa

ALLOWED_HOSTS = ["testserver", "localhost", "127.0.0.1"]
DATABASES = {"default": {
    "ENGINE": "django.db.backends.sqlite3",
    "NAME": os.path.join(os.path.dirname(__file__), "verif.sqlite3"),
}}
PY

export DJANGO_SETTINGS_MODULE=settings_verif
export PYTHONPATH="$SCRATCH:$RAIZ"

PY="$RAIZ/venv/bin/python"
[ -x "$PY" ] || PY="$(command -v python3)"

paso() { printf '\n== %s ==\n' "$1"; }

paso "check"
"$PY" manage.py check

paso "migraciones: sin cambios pendientes"
"$PY" manage.py makemigrations --check --dry-run

paso "migrate"
"$PY" manage.py migrate --noinput

paso "carga de datos"
"$PY" manage.py cargar_datos

if "$PY" -c "import pytest" >/dev/null 2>&1; then
  paso "pytest"
  "$PY" -m pytest -q
else
  paso "pytest (no instalado, se omite)"
fi

if "$PY" -m ruff --version >/dev/null 2>&1; then
  paso "ruff"
  "$PY" -m ruff check .
else
  paso "ruff (no instalado, se omite)"
fi

paso "smoke de rutas"
"$PY" - <<'PY'
import os, django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "settings_verif")
django.setup()
from django.test.utils import setup_test_environment
setup_test_environment()
from django.contrib.auth import get_user_model
from django.test import Client
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

# API v1: esquema, login por token y permisos.
assert c.get("/api/schema/").status_code == 200, "schema"
esquema = c.get("/api/schema/").content.decode()
for ruta_api in ["/api/v1/auth/recuperar/", "/api/v1/auth/validar/",
                 "/api/v1/auth/nueva-password/", "/api/v1/vecinos/"]:
    assert ruta_api in esquema, ("fuera del esquema", ruta_api)
a = Client()
r = a.post("/api/v1/auth/login/",
           {"email": "admin@test.cl", "password": "Clave.123"})
assert r.status_code == 200, ("login api", r.status_code)
auth = {"HTTP_AUTHORIZATION": f"Bearer {r.json()['access']}"}
assert a.get("/api/v1/auth/me/", **auth).status_code == 200, "me"
assert a.get("/api/v1/vecinos/").status_code == 401, "vecinos sin token"
assert a.get("/api/v1/vecinos/", **auth).status_code == 200, "vecinos con token"

# Recuperación de contraseña, de punta a punta.
from apps.cuentas.models import RecuperacionPassword
a.post("/api/v1/auth/recuperar/", {"email": "admin@test.cl"})
rec = RecuperacionPassword.objects.filter(usuario=u).order_by("-creado").first()
assert rec is not None, "sin recuperación"
assert a.post("/api/v1/auth/validar/",
              {"email": "admin@test.cl", "codigo": rec.codigo}).status_code == 200, "validar"
assert a.post("/api/v1/auth/nueva-password/",
              {"email": "admin@test.cl", "codigo": rec.codigo,
               "password": "Nueva.Clave.123"}).status_code == 200, "nueva password"
assert a.post("/api/v1/auth/login/",
              {"email": "admin@test.cl", "password": "Nueva.Clave.123"}).status_code == 200, "login nuevo"

# Permisos por rol: una cuenta de solo lectura no escribe ni ve usuarios.
from apps.cuentas.models import Rol as RolModel
rol_consulta, _ = RolModel.objects.get_or_create(
    codigo="consulta", defaults={"nombre": "CONSULTA"}
)
consulta, _ = U.objects.get_or_create(
    email="consulta@test.cl", defaults={"first_name": "C", "last_name": "D"}
)
consulta.rol = rol_consulta
consulta.set_password("Clave.123")
consulta.is_active = True
consulta.save()
b = Client()
rb = b.post("/api/v1/auth/login/", {"email": "consulta@test.cl", "password": "Clave.123"})
assert rb.status_code == 200, ("login consulta", rb.status_code)
authb = {"HTTP_AUTHORIZATION": f"Bearer {rb.json()['access']}"}
assert b.get("/api/v1/vecinos/", **authb).status_code == 200, "consulta lee vecinos"
assert b.post("/api/v1/vecinos/", {"nombre": "x"}, **authb).status_code == 403, "consulta no escribe"
assert b.get("/api/v1/usuarios/", **authb).status_code == 403, "consulta no ve usuarios"
b.post("/login/", {"username": "consulta@test.cl", "password": "Clave.123"}, follow=True)
assert b.get("/usuarios/").status_code == 403, "web: usuarios prohibido"
assert b.get("/vecinos/").status_code == 200, "web: vecinos permitido"
print("SMOKE OK")
PY

printf '\nVERIFICACIÓN OK\n'
