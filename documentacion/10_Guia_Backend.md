# 10 · Guía del backend — recorrido del código

Documento de estudio. Recorre el proyecto completo, archivo por archivo, en el orden en
que el sistema los ejecuta, con los fragmentos reales y de dónde sale cada uno. Deja fuera
plantillas y CSS: las vistas aparecen solo como el puente hacia el ORM.

**El hilo, en una línea:** `.env → settings.DATABASES → modelos (tablas) → migraciones (las
crean) → ORM (objects / todos) → Admin y vistas leen y escriben → cargar_datos llena desde JSON`.

---

## 0. `manage.py` y `config/wsgi.py` — la puerta de entrada

Todo comando (`runserver`, `migrate`, `cargar_datos`) entra por `manage.py`:

```python
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
from django.core.management import execute_from_command_line
execute_from_command_line(sys.argv)
```

Lo único que hace es decirle a Django dónde están los settings y pasarle los argumentos.
`config/wsgi.py` repite la misma idea, pero para el servidor de producción:

```python
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
application = get_wsgi_application()
```

Ese `application` es lo que ejecuta `gunicorn config.wsgi:application` en el EC2.

---

## 1. `config/settings.py` — el corazón

Aquí vive la conexión a la base de datos:

```python
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
```

- `ENGINE` dice «habla MySQL»; MariaDB habla el mismo protocolo.
- Los cinco valores **no** están escritos aquí: salen de `env(...)`, que lee el `.env`.
- Los `OPTIONS` fuerzan UTF-8 completo y modo estricto (MySQL no guarda datos inválidos en silencio).

La lectura del `.env`:

```python
load_dotenv(BASE_DIR / ".env")

def env(nombre, default=""):
    return os.environ.get(nombre, default)
```

`BASE_DIR` es la raíz del proyecto, la misma que usa el comando de carga.

Los modelos que Django administra, más los propios:

```python
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
    "apps.panel",
]
```

Las seis primeras son de Django (crean `django_migrations`, `django_session`, `auth_*`,
`django_content_type`, etc.). Las cinco propias se registran por **ruta completa**
(`apps.cuentas`), no como `cuentas`, porque viven bajo `apps/`.

La pieza clave del usuario propio:

```python
AUTH_USER_MODEL = "cuentas.Usuario"
```

Le dice a Django que el usuario del sistema es el propio, y obliga a fijarlo antes de la
primera migración.

Además, en este archivo se definen: `AUTH_PASSWORD_VALIDATORS` (con el validador
institucional propio), `LOGIN_URL` / `LOGIN_REDIRECT_URL` / `LOGOUT_REDIRECT_URL`,
`MAILERS` (el correo, por `.env`), `OTP_EXPIRY_MINUTES` y `USUARIOS_PASSWORD_INICIAL`.

---

## 2. `.env` y `.env.example`

```bash
DB_NAME=abstergo
DB_USER=abstergo
DB_PASSWORD=
```

`.env.example` se versiona con las llaves vacías; el `.env` real queda fuera por el
`.gitignore` (`# Variables de entorno → .env`). Por eso la configuración nunca está en el
código.

---

## 3. `config/urls.py` y `apps/*/urls.py` — el ruteo

```python
urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("apps.cuentas.urls")),
    path("", include("apps.panel.urls")),
    path("", include("apps.organizacion.urls")),
    path("", include("apps.catalogos.urls")),
    path("", include("apps.ciudadanos.urls")),
]
```

`admin.site.urls` es el Admin de Django. Todo lo demás se reparte entre las apps con
`include()`. Cada app declara sus rutas:

```python
path("roles/", views.RolesListado.as_view(), name="roles"),
path("roles/nuevo/", views.RolesAlta.as_view(), name="roles_nueva"),
path("roles/<int:pk>/editar/", views.RolesEdicion.as_view(), name="roles_editar"),
path("roles/<int:pk>/eliminar/", views.RolesBorrado.as_view(), name="roles_eliminar"),
```

---

## 4. `apps/common/soft_delete.py` — la base de todos los modelos

Antes de los modelos, esto, porque los demás heredan de acá:

```python
class Eliminado(models.Model):
    eliminado = models.DateTimeField("eliminado", null=True, blank=True)

    class Meta:
        abstract = True

    def eliminar(self):
        self.eliminado = timezone.now()
        self.save(update_fields=["eliminado"])
```

`abstract = True` significa **no crea tabla**: es solo para heredar. `eliminar()` no borra:
escribe una fecha.

```python
class ActivosManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(eliminado__isnull=True)

class BorradoLogico(Eliminado):
    objects = ActivosManager()
    todos = TodosManager()

    class Meta:
        abstract = True
```

El detalle más fino del proyecto: `objects` **esconde** los dados de baja; `todos` los
muestra. Cualquier consulta normal (`Vecino.objects...`) ya viene filtrada. Por eso los
conteos del ORM pueden diferir de lo que se ve en phpMyAdmin.

---

## 5. Los modelos (`apps/*/models.py`)

Cada clase es una tabla. `apps/organizacion/models.py`:

```python
class Delegacion(BorradoLogico):
    codigo = models.CharField("código", max_length=40, unique=True)
    nombre = models.CharField("nombre", max_length=120)
    direccion = models.CharField("dirección", max_length=200, blank=True)
    comuna = models.CharField("comuna", max_length=80, blank=True)
```

No se declara `id`: Django lo agrega solo. El primer texto entre comillas es la etiqueta
visible.

Las relaciones, en `apps/ciudadanos/models.py`:

```python
territorio = models.ForeignKey(
    "organizacion.Delegacion",
    on_delete=models.PROTECT,
    related_name="vecinos",
    verbose_name="territorio",
)
```

- `ForeignKey` = la columna `territorio_id`.
- `PROTECT` = la base se niega a borrar una Delegación que tenga vecinos.
- `related_name="vecinos"` habilita el acceso inverso `delegacion.vecinos.all()`.

El usuario, en `apps/cuentas/models.py`, es el más especial:

```python
class Usuario(AbstractUser, Eliminado):
    username = None
    email = models.EmailField("correo", unique=True, null=True, blank=True)
    rol = models.ForeignKey(Rol, on_delete=models.PROTECT, ...)
    delegacion = models.ForeignKey("organizacion.Delegacion", on_delete=models.PROTECT, ...)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []
    objects = UsuarioManager()
```

- `AbstractUser` aporta `password`, `is_active`, `is_staff`, `first_name`, `last_name`,
  `date_joined`, `groups`... (por eso aparecen en la migración).
- `username = None` lo elimina; la llave pasa a ser el `id` y el correo es un dato editable.
- `USERNAME_FIELD = "email"` hace que el login sea por correo.
- Hereda de `Eliminado` y **no** de `BorradoLogico`, porque su `objects` tiene que seguir
  siendo un `UserManager`.

Ese manager es propio:

```python
class UsuarioManager(UserManager):
    def create_user(self, email=None, password=None, **extra_fields):
        if not email:
            raise ValueError("El correo es obligatorio.")
        usuario = self.model(email=self.normalize_email(email), **extra_fields)
        usuario.set_password(password)
        usuario.save(using=self._db)
        return usuario

    def create_superuser(self, email=None, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        return self.create_user(email, password, **extra_fields)
```

Sin esto, `createsuperuser` fallaría: el manager de Django exige `username`.

Los 7 modelos: `Delegacion`, `Rol`, `Usuario`, `Meta`, `TipoAtencion`, `SubAtencion`,
`Vecino`.

---

## 6. Las migraciones (`apps/*/migrations/0001_initial.py`)

Es el modelo traducido a SQL, generado con `makemigrations` y aplicado con `migrate`:

```python
dependencies = [
    ('auth', '0012_alter_user_first_name_max_length'),
    ('organizacion', '0001_initial'),
]

operations = [
    migrations.CreateModel(
        name='Rol',
        fields=[
            ('id', models.BigAutoField(auto_created=True, primary_key=True, ...)),
            ('eliminado', models.DateTimeField(blank=True, null=True, ...)),
            ('nombre', models.CharField(max_length=60, unique=True, ...)),
        ],
        ...
    ),
]
```

- `dependencies`: `cuentas` **depende** de `organizacion`, porque `Usuario` tiene una FK a
  `Delegacion`. Ese orden hace que `migrate` cree primero una tabla y después la otra.
- `managers=[('objects', apps.cuentas.models.UsuarioManager())]` deja constancia del
  manager dentro de la migración.

Hay cuatro `0001_initial.py`: `cuentas`, `organizacion`, `catalogos` y `ciudadanos`
(`panel` no tiene modelos).

---

## 7. El Admin (`apps/common/admin_base.py` + cada `admin.py`)

Todo el Admin hereda de una sola clase, que trae el CRUD y el borrado lógico:

```python
class AdminBase(admin.ModelAdmin):
    list_per_page = 25

    def delete_model(self, request, obj):
        obj.eliminar()

    def delete_queryset(self, request, queryset):
        queryset.update(eliminado=timezone.now())
```

Cada modelo se registra en su `admin.py`:

```python
@admin.register(Vecino)
class VecinoAdmin(AdminBase):
    list_display = ("nombre", "rut", "direccion", "telefono", "territorio", "tipo_gestion", "estado")
    search_fields = ("nombre", "rut", "direccion", "telefono", "territorio__nombre", "tipo_gestion")
    list_filter = ("territorio", "estado")
    autocomplete_fields = ("territorio",)
```

- El `__` de `territorio__nombre` cruza la FK (mismo mecanismo del ORM).
- `autocomplete_fields` necesita `search_fields` en el modelo apuntado.
- El borrado no emite `DELETE`: marca `eliminado`, igual que el front.

---

## 8. Los datos de origen (`datos_nuevos/*.json`)

Un archivo por entidad, con los mismos nombres que las columnas:

```json
[
  {
    "codigo": "centro",
    "nombre": "Centro",
    "direccion": "Cienfuegos 550",
    "comuna": "La Serena"
  }
]
```

En `usuarios.json` el rol y la delegación vienen como **texto**, no como id:

```json
{ "nombre": "Carlos Mendoza", "email": "carlos@muniserena.cl",
  "rol": "ADMIN", "delegacion": "centro", "activo": true }
```

Convertir ese texto en una FK es justamente el trabajo del comando.

---

## 9. El comando `apps/panel/management/commands/cargar_datos.py`

El ejemplo más completo de ORM del proyecto:

```python
class Command(BaseCommand):
    help = "Carga datos_nuevos/ en la base de datos. Reejecutable sin duplicar."

    @transaction.atomic
    def handle(self, *args, **options):
        self.cargar("delegaciones", Delegacion, "codigo",
                    lambda f: {"nombre": f["nombre"], "direccion": f["direccion"], "comuna": f["comuna"]})
        ...
```

- `BaseCommand` + `handle()` es la firma de todo comando de gestión.
- `@transaction.atomic` = todo o nada.

El método central:

```python
def cargar(self, archivo, modelo, clave, armar):
    con_baja = hasattr(modelo, "eliminado")
    gestor = modelo.todos if con_baja else modelo.objects
    for fila in leer(archivo):
        valores = armar(fila)
        if con_baja:
            valores["eliminado"] = None
        _, creado = gestor.update_or_create(**{clave: fila[clave]}, defaults=valores)
        self.anotar(creado)
```

Tres ideas juntas:

1. `update_or_create` → busca por la clave y crea o actualiza: **reejecutable sin duplicar**.
2. `modelo.todos` → el gestor sin filtro, para **restaurar** lo dado de baja y limpiar `eliminado`.
3. Los `lambda` traducen texto a FK:

```python
self.cargar("vecinos", Vecino, "rut",
    lambda f: {
        "nombre": f["nombre"],
        "direccion": f["direccion"],
        "telefono": f["telefono"],
        "territorio": Delegacion.objects.get(codigo=f["territorio"]),
        "tipo_gestion": f["tipo_gestion"],
        "estado": f["estado"],
    })
```

`Delegacion.objects.get(codigo=...)` busca la fila y devuelve el objeto; el ORM guarda su
`id` en la columna `territorio_id`.

Los usuarios se cargan aparte, con la llave por nombre completo (no por correo, que puede
ser nulo):

```python
usuario, creado = Usuario.objects.update_or_create(
    first_name=nombre,
    last_name=apellido,
    defaults={"email": correo, "rol": Rol.objects.get(nombre=fila["rol"]), ...},
)
if creado:
    usuario.set_password(settings.USUARIOS_PASSWORD_INICIAL if correo else None)
    usuario.save()
```

---

## 10. `apps/common/vistas_base.py` — donde Django consulta

Aquí se ve cómo una petición termina en el ORM:

```python
class ListadoBase(Comun, LoginRequiredMixin, ListView):
    busqueda = ()
    relacionadas = ()

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
```

- `select_related` evita una consulta por fila (hace un JOIN).
- `Q(...) | Q(...)` arma el `OR` del buscador.
- `icontains` es el `LIKE` (sin distinguir mayúsculas).

El borrado lógico en el alta, la edición y el borrado:

```python
def form_valid(self, form):
    if hasattr(self.object, "eliminar"):
        self.object.eliminar()
    else:
        self.object.delete()
    return redirect(self.url_listado)
```

Y una excepción que enseña mucho, de `apps/cuentas/views.py`:

```python
class UsuariosListado(ListadoBase):
    def get_queryset(self):
        # Usuario conserva el UserManager, que no filtra por borrado lógico.
        return super().get_queryset().filter(eliminado__isnull=True)
```

---

## 11. Autenticación (`apps/cuentas/views.py`)

El flujo de recuperación, con la lógica de backend a la vista:

```python
def _guardar_otp(request, usuario):
    codigo = f"{secrets.randbelow(1000000):06d}"
    sesion = request.session
    sesion["otp_codigo"] = codigo
    sesion["otp_usuario"] = usuario.pk
    sesion["otp_expira"] = (
        timezone.now() + timedelta(minutes=settings.OTP_EXPIRY_MINUTES)
    ).timestamp()
    send_mail("Código de verificación",
              f"Tu código de verificación es {codigo}...",
              None, [usuario.email])
```

El código vive en la **sesión** (por eso no necesita tabla propia) y `send_mail` usa el
backend del `.env`.

La validación:

```python
if timezone.now().timestamp() > sesion.get("otp_expira", 0):
    form.add_error(None, "El código venció. Pide uno nuevo.")
    return self.form_invalid(form)
if form.cleaned_data["codigo"] != sesion["otp_codigo"]:
    form.add_error(None, "El código no coincide.")
    return self.form_invalid(form)
del sesion["otp_codigo"]        # sirve una sola vez
sesion["otp_validado"] = True
```

Y el guardado, con hash:

```python
usuario.set_password(form.cleaned_data["password1"])
usuario.save()
```

`set_password` hashea (PBKDF2); nunca se guarda la contraseña en claro.

---

## 12. `apps/cuentas/validators.py`

Se conecta desde `settings.py`, dentro de `AUTH_PASSWORD_VALIDATORS`:

```python
class RequisitosInstitucionalesValidator:
    def validate(self, password, user=None):
        faltantes = []
        if not any(c.isupper() for c in password):
            faltantes.append("una letra mayúscula")
        if not any(c.islower() for c in password):
            faltantes.append("una letra minúscula")
        if not any(not c.isalnum() for c in password):
            faltantes.append("un carácter especial")
        if faltantes:
            raise ValidationError("La contraseña debe incluir " + ", ".join(faltantes) + ".")

    def get_help_text(self):
        return "Debe incluir una letra mayúscula, una minúscula y un carácter especial."
```

---

## 13. `apps/*/apps.py`

```python
class CuentasConfig(AppConfig):
    name = 'apps.cuentas'
    verbose_name = 'Cuentas'
```

Es lo que aparece en el Admin como nombre de sección. `apps/common/` **no** tiene `apps.py`
ni está en `INSTALLED_APPS`: es solo un paquete de código compartido, no una app.

---

## Cierre

**El recorrido completo:** `.env → settings.DATABASES → modelos (tablas) → migraciones (las
crean) → ORM (objects / todos) → Admin y vistas leen y escriben → cargar_datos llena desde
JSON`.

**Dos detalles a tener presentes:**

- `requirements.txt` **no** incluye `mysqlclient`. Sin ese driver, el `ENGINE` mysql no
  conecta; se instala aparte en el despliegue. Quien clone y haga solo `pip install -r
  requirements.txt` no levanta.
- El comentario de `settings.py` dice «MAILERS reemplaza a `EMAIL_BACKEND` desde Django
  6.0», mientras el documento técnico dice 6.1. Conviene unificar cuál versión es.
