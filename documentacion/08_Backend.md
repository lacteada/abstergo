# 08 · Back-end — guía de estudio

Material para estudiar cómo está armado el back-end.
Amplía los §2 a §5 y §7 de `documento_tecnico.md`; el front tiene su propia guía
en `07_Frontend.md`.

## 1. En una frase

Django 6.1 con 5 apps y 7 modelos, vistas genéricas que heredan de una base
común, un comando de carga idempotente y un Admin en solo lectura. Los datos se
leen siempre por el ORM y la configuración sale del `.env`.

## 2. Stack

- Python 3.14 · Django 6.1.1.
- MariaDB como motor, con `mysqlclient` como driver.
- `python-dotenv` para leer el `.env`.
- `gunicorn` para producción (detrás de Apache, junto a phpMyAdmin).

## 3. Mapa del proyecto

```text
abstergo/
├── manage.py
├── config/                  configuración del proyecto
│   ├── settings.py          lee el .env, define apps, BD, plantillas
│   ├── urls.py              enlaza el admin y las 5 apps
│   ├── wsgi.py / asgi.py
├── apps/
│   ├── common/              compartido; NO es una app de Django
│   │   ├── vistas_base.py   las 4 vistas genéricas de los mantenedores
│   │   ├── admin_base.py    el Admin en solo lectura
│   │   └── soft_delete.py   el borrado lógico
│   ├── cuentas/             Rol, PerfilUsuario, autenticación
│   ├── organizacion/        Delegacion
│   ├── catalogos/           Meta, TipoAtencion, SubAtencion
│   ├── ciudadanos/          Vecino
│   └── panel/               Inicio y el comando de carga
├── datos_nuevos/            JSON de importación, un archivo por entidad
├── templates/  static/  documentacion/
```

Clave de estructura: las apps se registran por su ruta completa (`apps.cuentas`),
y `apps/common/` no está en `INSTALLED_APPS`: es sólo el paquete de lo
compartido.

## 4. `config/`: settings y URLs

### `settings.py`

- `load_dotenv(BASE_DIR / ".env")` y un helper `env(nombre, default)`; nada
  sensible queda escrito en el código.
- `INSTALLED_APPS`: las apps propias con su ruta completa, más las de Django.
- `DATABASES`: `django.db.backends.mysql`, con los valores del `.env`.
- `TEMPLATES`: `DIRS` apunta a `templates/` y además `APP_DIRS`.
- `AUTH_PASSWORD_VALIDATORS`: los de Django más un validador propio
  (`apps.cuentas.validators.RequisitosInstitucionalesValidator`).
- `MAILERS` (Django 6.1 reemplazó `EMAIL_BACKEND`): consola en desarrollo, SMTP
  en el EC2.
- `LOGIN_URL`, `LOGIN_REDIRECT_URL`, `LOGOUT_REDIRECT_URL`.

### `urls.py`

El `ROOT_URLCONF` incluye, en este orden: `admin/`, y luego las 5 apps con
`include(...)`, cada una con su `app_name` (namespace): `panel`, `cuentas`,
`organizacion`, `catalogos`, `ciudadanos`.

## 5. Los 7 modelos

Viven repartidos en 4 apps. Todos con `verbose_name` en español y `ordering`.

### Organización

```python
class Delegacion(BorradoLogico):        # organizacion/models.py
    codigo = models.CharField("código", max_length=40, unique=True)
    nombre = models.CharField("nombre", max_length=120)
    direccion = models.CharField("dirección", max_length=200, blank=True)
    comuna = models.CharField("comuna", max_length=80, blank=True)
    activo = models.BooleanField("activo", default=True)
```

### Cuentas

```python
class Rol(BorradoLogico):               # cuentas/models.py
    nombre = models.CharField("nombre", max_length=60, unique=True)
    descripcion = models.CharField("descripción", max_length=200, blank=True)

class PerfilUsuario(models.Model):
    usuario = models.OneToOneField(User, on_delete=models.CASCADE, related_name="perfil")
    rol = models.ForeignKey(Rol, on_delete=models.PROTECT, null=True, blank=True)
    delegacion = models.ForeignKey("organizacion.Delegacion", on_delete=models.PROTECT,
                                   null=True, blank=True)
    estado = models.CharField("estado", max_length=10, choices=ESTADOS, default=ACTIVO)
```

El `Usuario` **no** se modela de cero: se usa el `auth.User` de Django y un
perfil `OneToOne` que aporta rol, delegación y estado. El perfil se crea solo,
con una señal:

```python
@receiver(post_save, sender=User)
def crear_perfil(sender, instance, created, **kwargs):
    if created:
        PerfilUsuario.objects.create(usuario=instance)
```

### Catálogos

```python
class Meta(models.Model):               # catalogos/models.py
    nombre = models.CharField("nombre", max_length=120)
    descripcion = models.CharField("descripción", max_length=200, blank=True)

class TipoAtencion(BorradoLogico):
    nombre = models.CharField("nombre", max_length=120)
    descripcion = models.CharField("descripción", max_length=200, blank=True)

class SubAtencion(models.Model):
    nombre = models.CharField("nombre", max_length=120)
    tipo_atencion = models.ForeignKey(TipoAtencion, on_delete=models.PROTECT,
                                      related_name="sub_atenciones")
```

### Ciudadanos

```python
class Vecino(models.Model):             # ciudadanos/models.py
    nombre = models.CharField("nombre", max_length=120)
    rut = models.CharField("RUT", max_length=15, unique=True)
    direccion = models.CharField("dirección", max_length=200, blank=True)
    telefono = models.CharField("teléfono", max_length=30, blank=True)
    territorio = models.ForeignKey("organizacion.Delegacion", on_delete=models.PROTECT,
                                   related_name="vecinos")
    tipo_gestion = models.CharField("tipo de gestión", max_length=80, blank=True)
    estado = models.CharField("estado", max_length=10, choices=ESTADOS, default=ACTIVO)
```

### Resumen de relaciones

```
PerfilUsuario → Rol            (PROTECT)
PerfilUsuario → Delegacion     (PROTECT)
SubAtencion   → TipoAtencion   (PROTECT)
Vecino        → Delegacion     (PROTECT)
PerfilUsuario → User           (CASCADE: el perfil no existe sin el usuario)
```

## 6. Integridad: `PROTECT` + borrado lógico

El problema: con `PROTECT`, no se puede dar de baja una Delegación o un Rol que
esté en uso. Cambiar a cascada borraría los vecinos; `SET_NULL` dejaría al
vecino sin territorio.

La solución: **borrado lógico** en las tres entidades que otras referencian
(`Delegacion`, `Rol`, `TipoAtencion`). En vez de borrar la fila, se marca una
fecha. La fila sale del listado pero nadie pierde la referencia.

`apps/common/soft_delete.py`:

```python
class TodosManager(models.Manager):
    """Ve también los eliminados."""

class ActivosManager(models.Manager):
    """Por defecto no muestra los eliminados."""
    def get_queryset(self):
        return super().get_queryset().filter(eliminado__isnull=True)

class BorradoLogico(models.Model):
    eliminado = models.DateTimeField("eliminado", null=True, blank=True)
    objects = ActivosManager()     # por defecto, sin dados de baja
    todos = TodosManager()         # incluye los dados de baja

    class Meta:
        abstract = True

    def eliminar(self):
        self.eliminado = timezone.now()
        self.save(update_fields=["eliminado"])
```

Efectos asumidos:

- Una Delegación dada de baja sigue ocupando su `codigo`, y un Rol su `nombre`.
- `cargar_datos` restaura lo dado de baja (usa el gestor `todos` y limpia la
  fecha), así el comando sigue siendo idempotente.
- En las otras cuatro entidades el borrado es real (`delete()`).

## 7. Migraciones

Cuatro `0001_initial.py`, uno por app con modelos: `cuentas`, `organizacion`,
`catalogos` y `ciudadanos`. Se aplican con `manage.py migrate`.

## 8. Vistas: genéricas + una base compartida

Los 7 mantenedores tienen 4 vistas cada uno (listado, alta, edición, borrado) =
28 vistas. Todas son genéricas de Django y heredan de una base común.

`apps/common/vistas_base.py`:

```python
class Comun:
    titulo = ""
    subtitulo = ""
    seccion = ""
    etiqueta_nueva = ""     # texto del botón "+ Nuevo ..."
    url_listado = ""

class ListadoBase(Comun, LoginRequiredMixin, ListView):
    template_name = "listado.html"
    busqueda = ()           # campos donde busca el ?q=
    relacionadas = ()       # FKs para select_related (evita N+1)

    def get_queryset(self):
        queryset = super().get_queryset()
        if self.relacionadas:
            queryset = queryset.select_related(*self.relacionadas)
        q = self.request.GET.get("q")
        if q and self.busqueda:
            condicion = Q()
            for campo in self.busqueda:
                condicion |= Q(**{f"{campo}__icontains": q})
            queryset = queryset.filter(condicion)
        return queryset

    def get_context_data(self, **kwargs):
        contexto = super().get_context_data(**kwargs)
        contexto.update(
            titulo=self.titulo, subtitulo=self.subtitulo, seccion=self.seccion,
            etiqueta_nueva=self.etiqueta_nueva,
            url_nueva=reverse(self.url_nueva), url_listado=self.url_listado,
        )
        return contexto

class _FormularioBase(Comun, LoginRequiredMixin): ...
class AltaBase(_FormularioBase, CreateView): ...
class EdicionBase(_FormularioBase, UpdateView): ...
class BorradoBase(Comun, LoginRequiredMixin, DeleteView): ...
```

Y cada `views.py` declara **sólo sus datos**:

```python
class UsuariosListado(ListadoBase):
    model = PerfilUsuario
    template_name = "cuentas/usuarios_lista.html"
    titulo = "Usuarios"
    seccion = "usuarios"
    etiqueta_nueva = "Nuevo usuario"
    busqueda = ("usuario__first_name", "usuario__last_name", "usuario__email")
    relacionadas = ("usuario", "rol", "delegacion")
    url_nueva = "cuentas:usuarios_nueva"
    url_listado = "cuentas:usuarios"
```

Conceptos para estudiar:

- **Search**: `get_queryset` arma un `Q` con `OR` de `icontains` sobre los campos
  declarados. Cruzar una FK (`territorio__nombre`) hace que el ORM agregue el
  `JOIN`. Buscar "rural" en Vecinos encuentra por **nombre del territorio**.
- **N+1**: `select_related` trae las FKs que la plantilla recorre en la misma
  consulta, en vez de una consulta por fila.
- **LoginRequiredMixin**: cada vista exige sesión; si no hay, redirige a
  `LOGIN_URL`.
- **Borrado lógico en la vista**: `BorradoBase.form_valid` llama a `eliminar()`
  si el modelo tiene ese método, y a `delete()` si no.

## 9. URLs

Un `urls.py` por app, con `app_name` (namespace) y `name` por ruta. En los
templates se invocan como `{% url 'cuentas:usuarios_editar' fila.pk %}`. Ese
`name` es el que usan `reverse()` en las vistas y `{% url %}` en las plantillas;
cambiar una ruta no obliga a tocar las plantillas.

## 10. Comando `cargar_datos`

`apps/panel/management/commands/cargar_datos.py`. Lee `datos_nuevos/*.json` y
escribe con el ORM.

```python
@transaction.atomic
def handle(self, *args, **options):
    self.cargar("delegaciones", Delegacion, "codigo", lambda f: {...})
    self.cargar("roles", Rol, "nombre", lambda f: {"descripcion": f["descripcion"]})
    self.cargar_usuarios()
    self.cargar("metas", Meta, "nombre", ...)
    self.cargar("tipos_atencion", TipoAtencion, "nombre", ...)
    self.cargar("sub_atenciones", SubAtencion, "nombre", ...)
    self.cargar("vecinos", Vecino, "rut", ...)
```

Claves:

- `update_or_create` dentro de `cargar` → **idempotente**: correrlo dos veces no
  duplica.
- Recorre en orden de dependencia: primero lo que no tiene FK, al final `Vecino`.
- `@transaction.atomic`: si algo falla, no deja datos a medias.
- A los usuarios migrados les asigna la contraseña del `.env`
  (`USUARIOS_PASSWORD_INICIAL`).

## 11. Admin en solo lectura

`apps/common/admin_base.py`:

```python
class SoloLecturaAdmin(admin.ModelAdmin):
    list_per_page = 25
    def has_add_permission(self, request): return False
    def has_change_permission(self, request, obj=None): return False
    def has_delete_permission(self, request, obj=None): return False
```

Las 7 clases del Admin heredan de esta base, así que las tres restricciones se
escriben una sola vez. Es una decisión consciente: revertirlo es quitar esos
tres métodos.

## 12. Autenticación

- **Login**: `django.contrib.auth.views.LoginView` con un formulario propio
  (`FormularioLogin`) para cambiar las etiquetas. En los datos migrados el
  `username` es el correo.
- **Logout**: `LogoutView`, por **POST** (Django 5+).
- **Recuperar / Validar / Nueva contraseña**: `FormView` propias en
  `apps/cuentas/views.py`.

El código OTP:

- Se genera con `secrets.randbelow(1000000)` formateado a 6 dígitos.
- Vive en la **sesión** (`otp_codigo`, `otp_usuario`, `otp_expira`), no en una
  tabla.
- Vence a los `OTP_EXPIRY_MINUTES` minutos y se borra al usarlo: no se reutiliza.
- La respuesta al pedir el código es la misma exista o no el correo, para no
  revelar qué cuentas hay.
- El `Reenviar` regenera el código desde la sesión, sin volver a pedir el correo.

## 13. El ORM y el SQL

No hay SQL escrito a mano ni uso de `cursor()`/`raw()`. Ejemplo real:

```python
Vecino.objects.filter(territorio__nombre="Centro")
```

Django genera:

```sql
SELECT "ciudadanos_vecino"."id", ...
FROM "ciudadanos_vecino"
INNER JOIN "organizacion_delegacion"
  ON ("ciudadanos_vecino"."territorio_id" = "organizacion_delegacion"."id")
WHERE "organizacion_delegacion"."nombre" = Centro
ORDER BY "ciudadanos_vecino"."nombre" ASC
```

Detalle: Django **no** emite `ON DELETE` en la base; resuelve el borrado desde
Python. Por eso `PROTECT`/`CASCADE` se comportan igual en MariaDB y en SQLite.

## 14. Flujo de una petición (de punta a punta)

Listado de Vecinos, `GET /vecinos/?q=rural`:

1. `config/urls.py` → `apps.ciudadanos.urls` → `views.Listado.as_view()`.
2. `LoginRequiredMixin` verifica la sesión; si no hay, redirige a `LOGIN_URL`.
3. `ListadoBase.get_queryset`: `select_related("territorio")` y, con `q=rural`,
   `filter(Q(nombre__icontains=... ) | Q(territorio__nombre__icontains="rural") | ...)`.
4. `get_context_data` agrega `titulo`, `seccion`, `etiqueta_nueva`, `url_nueva`,
   `url_listado`.
5. `listado.html` renderiza el armazón y `ciudadanos/vecinos_lista.html` llena
   `encabezado` y `fila`.
6. Si la petición la hizo `busqueda.js`, sólo se toman `[data-filas]` y
   `[data-pie]` del HTML resultante.

## 15. Entornos: MariaDB (prod) frente a SQLite (local)

El proyecto está configurado **sólo** a MariaDB: `settings.py` tiene
`ENGINE=django.db.backends.mysql` fijo y el `.env` apunta a `127.0.0.1:3306`.
No hay config SQLite en el repo ni `db.sqlite3`.

Para verlo en local sin MariaDB, una sesión anterior usó un SQLite temporal,
**fuera del repo**. Se armó en el scratchpad del agente:

```python
# settings_sqlite.py
from config.settings import *
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": __import__("pathlib").Path(__file__).with_name("abstergo.sqlite3"),
    }
}
```

Y se levantaba así (el `PYTHONPATH` deja importar `settings_sqlite` como módulo
suelto):

```bash
PYTHONPATH=<scratchpad> \
DJANGO_SETTINGS_MODULE=settings_sqlite \
./venv/bin/python manage.py runserver 8000 --noreload
```

Consecuencias a tener presentes:

- Sin `mysqlclient` y sin MariaDB, `runserver` con `config.settings` **aborta**
  (`Error loading MySQLdb module`). Sólo funciona el override a SQLite.
- `--noreload` sirve bien los cambios de plantillas y CSS (se leen por
  request), pero **no** recarga el código Python: al cambiar vistas o modelos hay
  que reiniciar el proceso.
- El SQLite vive en un directorio temporal: no es durable ni forma parte del
  repositorio.
- En producción se usa MariaDB, `mysqlclient` y `gunicorn`.

## 16. Checklist de estudio

- [ ] Sé por qué `apps/common` no es una app y qué contiene.
- [ ] Sé qué entidades tienen borrado lógico y por qué.
- [ ] Sé cómo una vista de listado filtra y evita el N+1.
- [ ] Sé por qué `cargar_datos` es idempotente.
- [ ] Sé cómo viaja el OTP y por qué se guarda en la sesión.
- [ ] Sé por qué local corrió en SQLite pese a que el proyecto apunta a MariaDB.
