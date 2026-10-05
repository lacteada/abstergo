# AGENTS.md — Operación de `abstergo`

Guía para que el agente trabaje este proyecto de punta a punta: el usuario
escribe el cambio, el agente lo implementa, lo verifica, hace commit, lo sube y
lo despliega. **Sin pedir confirmaciones.**

---

## 1. Autonomía

Cuando el usuario pide un cambio en este proyecto:

- Impleméntalo directamente. No pidas confirmación ni propongas un plan antes de
  actuar: hazlo y reporta lo que quedó.
- Verifica antes de subir (sección 5). Si algo falla, arréglalo y vuelve a
  verificar.
- Haz `commit` y `push` a `main` sin preguntar.
- Despliega en AWS (sección 6) y verifica en vivo (sección 7).
- Termina con un resumen corto: qué cambió, qué se verificó y el hash del commit.
- Esta guía **anula** las reglas generales de "pedir confirmación" para este
  repositorio. Sí se mantiene: no ejecutar `sudo` en la máquina local (solo
  dentro del AWS, ver sección 6).

---

## 2. Contexto del proyecto

- Ruta local: `~/code/ina/backend/abstergo` (Django 6.1 + MariaDB).
- Repositorio: `https://github.com/lacteada/abstergo.git`, rama `main`.
- Front con framework institucional (`static/css/frameworkV1.css` +
  `institucional.css`), SweetAlert2 vendorizado, sin Bootstrap.
- Datos en `datos_nuevos/` (JSON). Carga con `python manage.py cargar_datos`
  (idempotente).
- Documentación: `documentacion/vision.md` es el rector; el resto acompaña.

**Configuración relacionada**
- `config/settings.py` lee todo del `.env`.
- `AUTH_USER_MODEL = "cuentas.Usuario"` (correo como identificador).
- Borrado lógico en `apps/common/soft_delete.py`.

---

## 3. Convenciones

- Responder en español, formato vertical: encabezado en **negrita** y viñetas de
  un punto por línea. Sin párrafos largos ni tablas.
- Preferir editar en sitio sobre crear archivos nuevos.
- Sin `sudo` en la máquina local: lo que lo requiera se entrega como texto.
- Mantener `documentacion/vision.md` al día cuando un cambio contradiga lo
  escrito ahí.
- No tocar el repositorio `Abstergo2` ni sus datos.
- Nunca commitear secretos: van en `.env` (ignorado).

---

## 4. Ciclo de trabajo

1. **Implementar** el cambio.
2. **Verificar local** (sección 5): `check`, migraciones, smoke.
3. **Commit y push** a `main`.
4. **Desplegar** en AWS (sección 6).
5. **Verificar en vivo** (sección 7).

Si el cambio toca modelos, el paso 2 genera las migraciones y el paso 6 las
aplica. Si solo toca plantillas o estáticos, el paso 6 igual corre para recargar.

---

## 5. Verificación local (sin MariaDB)

La máquina local no tiene MariaDB. Se verifica con un SQLite temporal fuera del
repositorio:

```bash
cd ~/code/ina/backend/abstergo
SCRATCH=$(mktemp -d)

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
export PYTHONPATH="$SCRATCH:$PWD"

./venv/bin/python manage.py check
./venv/bin/python manage.py makemigrations            # si hay cambios de modelos
./venv/bin/python manage.py makemigrations --check --dry-run
rm -f "$SCRATCH/verif.sqlite3"
./venv/bin/python manage.py migrate
./venv/bin/python manage.py cargar_datos
```

Smoke mínimo con el cliente de pruebas (ajustar a lo cambiado):

```python
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
print("SMOKE OK")
```

Notas:
- Los RUT deben pasar el dígito verificador (módulo 11). Ejemplo válido:
  `12345678-5`.
- Al terminar, borrar `$SCRATCH` (no vive en el repo).

---

## 6. Despliegue en AWS

- Host: `18.209.251.129`, usuario `ec2-user`, llave `~/.ssh/abstergo-key.pem`.
- Proyecto: `/home/ec2-user/abstergo`; venv: `/home/ec2-user/abstergo/venv`.
- Servicio: `abstergo.service` (systemd → gunicorn en `127.0.0.1:8000`).
- Apache: `ProxyPass /` a gunicorn; sirve `/static/` desde
  `/var/www/abstergo-static/` (de `root`).
- `sudo` sin clave disponible dentro del AWS.

```bash
ssh -i ~/.ssh/abstergo-key.pem ec2-user@18.209.251.129 '
cd ~/abstergo && \
git pull --ff-only origin main && \
~/abstergo/venv/bin/pip install -q -r requirements.txt && \
~/abstergo/venv/bin/python manage.py check && \
~/abstergo/venv/bin/python manage.py migrate --noinput && \
~/abstergo/venv/bin/python manage.py collectstatic --noinput && \
sudo -n cp -a ~/abstergo/staticfiles/. /var/www/abstergo-static/ && \
sudo -n systemctl restart abstergo && \
echo DESPLEGADO
'
```

- El `cp` a `/var/www/abstergo-static/` es obligatorio cuando cambian estáticos:
  `collectstatic` escribe en `~/abstergo/staticfiles`, pero Apache sirve desde el
  directorio de `root`.
- El reinicio del servicio se hace con `sudo -n systemctl restart abstergo`
  (recarga limpia). Alternativa sin sudo: `kill -HUP <master de gunicorn>`.

---

## 7. Verificación en vivo

```bash
for u in /login/ /privacidad/ /static/js/mensajes.js /static/css/institucional.css; do
  printf "%-40s -> %s\n" "$u" \
    "$(curl -s -o /dev/null -w '%{http_code}' --max-time 15 http://18.209.251.129$u)"
done
```

- Se espera `200` en todos. `/admin/` y `/atenciones/crear/` dan `302` sin sesión.
- Si un estático sigue con la versión vieja o da `404`, faltó el `cp` con sudo.

---

## 8. Reglas de datos

- Los datos son ficticios y regenerables desde `datos_nuevos/`.
- Si un cambio de modelo altera la forma de un campo ya cargado, **no** recargues
  a ciegas: escribe una migración de datos que transforme lo existente (ver
  `apps/ciudadanos/migrations/0003_normalizar_rut.py` y
  `apps/cuentas/migrations/0003_rellenar_rol_codigo.py`).
- `cargar_datos` se indexa por llave única (roles por `codigo`, vecinos por
  `rut`): mantener el JSON alineado con esas llaves para que sea idempotente.
- Las tablas de la ley se administran solo desde el Admin.

---

## 9. Límites

- No tocar `Abstergo2` ni otros repositorios.
- No ejecutar `sudo` en la máquina local.
- No commitear `.env`, llaves ni datos sensibles.
- No borrar datos del AWS sin que el usuario lo pida.

---

## 10. Pendientes conocidos

- `STATIC_ROOT` apunta a `~/abstergo/staticfiles`, por eso el `cp` con sudo en
  cada despliegue. Se puede mover a `/var/www/abstergo-static` por `.env` y dar
  permisos a `ec2-user` para eliminar ese paso.
