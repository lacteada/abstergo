# Documento técnico — Abstergo

Sistema Municipal de Gestión de Atención Ciudadana.

Este documento describe el proyecto tal como está implementado en el código. Cada
afirmación se puede verificar en el archivo citado. La sección 17 describe el
diseño que sigue, todavía no implementado.

---

## 1. Descripción

**Qué es.** Una aplicación web Django para gestionar la atención ciudadana de
las delegaciones municipales de La Serena. Los datos viven en una base de datos
relacional (MariaDB) y se administran desde Django Admin y desde un front-end
propio con CRUD.

**Temática.** Atención ciudadana municipal: delegaciones, usuarios y roles,
metas por territorio, catálogos de tipos de atención y vecinos.

**Repositorio:** https://github.com/lacteada/abstergo

**Funcionalidades implementadas**

- 7 entidades modeladas con el ORM de Django, con llaves foráneas y borrado lógico.
- Carga de datos desde JSON con un comando de management idempotente.
- Django Admin con CRUD completo y borrado lógico.
- Front-end con un listado por entidad, buscador en vivo y CRUD (alta, edición,
  baja).
- Autenticación: login por correo, recuperar contraseña con código OTP de 6
  dígitos y cambio de contraseña.

---

## 2. Stack

Fuente: `requirements.txt`, `config/settings.py`.

| Componente | Versión / detalle |
|---|---|
| Python | 3.14 |
| Django | 6.1.1 |
| Base de datos | MariaDB, vía `django.db.backends.mysql` |
| Adaptador | `mysqlclient` (se instala aparte; compila contra MariaDB) |
| `gunicorn` | 26.2.0 (servidor en producción) |
| `python-dotenv` | 1.2.3 (lectura del `.env`) |
| `asgiref` | 3.12.1 |
| `sqlparse` | 0.6.0 |

Dependencias declaradas en `requirements.txt`:

```text
asgiref==3.12.1
Django==6.1.1
gunicorn==26.2.0
python-dotenv==1.2.3
sqlparse==0.6.0
```

---

## 3. Arquitectura y estructura

Configuración del proyecto (fuente: `config/settings.py`).

- `ROOT_URLCONF = "config.urls"`
- `WSGI_APPLICATION = "config.wsgi.application"`
- `AUTH_USER_MODEL = "cuentas.Usuario"` — modelo de usuario propio.
- Plantillas: `TEMPLATES[0]["DIRS"] = [BASE_DIR / "templates"]` y `APP_DIRS = True`.
- Estáticos: `STATIC_URL = "static/"`, `STATICFILES_DIRS = [BASE_DIR / "static"]`,
  `STATIC_ROOT = BASE_DIR / "staticfiles"`.

Aplicaciones propias instaladas (`INSTALLED_APPS`): `apps.organizacion`,
`apps.cuentas`, `apps.catalogos`, `apps.ciudadanos`, `apps.atenciones`,
`apps.cumplimiento`, `apps.panel` y `apps.api`.

Estructura de carpetas:

```text
abstergo/
├── manage.py
├── .env / .env.example / requirements.txt
├── config/                    # settings, urls, wsgi, asgi
├── apps/
│   ├── common/                # vistas base, Admin base, borrado lógico
│   │   ├── soft_delete.py
│   │   ├── admin_base.py
│   │   └── vistas_base.py
│   ├── cuentas/               # Rol, Usuario, recuperación (otp.py)
│   ├── organizacion/          # Delegacion
│   ├── catalogos/             # Meta, TipoAtencion, SubAtencion
│   ├── ciudadanos/            # Vecino
│   ├── atenciones/            # Atencion
│   ├── cumplimiento/          # tablas de la Ley 21.719
│   ├── api/                   # API v1 (DRF)
│   └── panel/                 # Inicio y comando cargar_datos
│       └── management/commands/cargar_datos.py
├── datos_nuevos/              # JSON de importación, uno por entidad
├── templates/                 # base.html, listado.html, por app
├── static/                    # css, js, img
└── documentacion/
```

`apps/panel` no tiene modelos ni migraciones: solo aporta la vista de inicio y el
comando de carga (`apps/panel/models.py` está vacío).

---

## 4. Modelo de datos

Trece modelos. Los siete del mantenedor (la tabla de abajo), más `Atencion`, las
cinco tablas de la Ley 21.719 (§17) y `RecuperacionPassword`. Todos heredan,
directa o indirectamente, del borrado lógico (`apps/common/soft_delete.py`), salvo
`RecuperacionPassword`. Ninguna relación borra en cascada: las llaves foráneas
usan `models.PROTECT`, salvo la de `RecuperacionPassword`, que puede irse con su
usuario.

| # | Entidad | App | Tabla | Campos propios |
|---|---|---|---|---|
| 1 | `Delegacion` | organizacion | `organizacion_delegacion` | `codigo` (único), `nombre`, `direccion`, `comuna`, `responsable`, `estado` |
| 2 | `Rol` | cuentas | `cuentas_rol` | `nombre` (único), `descripcion`, `codigo` (único) |
| 3 | `Usuario` | cuentas | `cuentas_usuario` | `email` (único, nulo), `rol`, `delegacion`, `delegaciones_autorizadas` (M2M) + campos de `AbstractUser` |
| 4 | `Meta` | catalogos | `catalogos_meta` | `codigo` (único), `nombre`, `descripcion`, `delegacion`, `estado` |
| 5 | `TipoAtencion` | catalogos | `catalogos_tipoatencion` | `codigo` (único), `nombre`, `descripcion`, `estado` |
| 6 | `SubAtencion` | catalogos | `catalogos_subatencion` | `codigo` (único), `nombre`, `tipo_atencion`, `estado` |
| 7 | `Vecino` | ciudadanos | `ciudadanos_vecino` | `nombre`, `rut` (único), `direccion`, `telefono`, `territorio`, `tipo_gestion`, `estado` |

Toda entidad lleva además la columna `eliminado` (`DateTimeField`, nulo) que
aporta el borrado lógico, y —salvo `Usuario` y `Vecino`, que tienen su propio
`estado`— la columna `estado` (`Activo`/`Inactivo`) que aporta `ConEstado`
(`apps/common/estados.py`). `estado` es el dato de negocio; `eliminado` es la
fila retirada del sistema.

### Relaciones (llaves foráneas)

Todas con `on_delete=models.PROTECT`:

| Desde | Hacia | Nulo | `related_name` |
|---|---|---|---|
| `Usuario.rol` | `Rol` | sí | `usuarios` |
| `Usuario.delegacion` | `Delegacion` | sí | `usuarios` |
| `Meta.delegacion` | `Delegacion` | no | `metas` |
| `SubAtencion.tipo_atencion` | `TipoAtencion` | no | `sub_atenciones` |
| `Vecino.territorio` | `Delegacion` | no | `vecinos` |

### El usuario propio

`apps/cuentas/models.py`.

- `Usuario(AbstractUser, Eliminado)` con `username = None`. La identidad es el
  `id`; el correo es un campo editable (`email`, único, admite `NULL`).
- Hereda de `Eliminado` y **no** de `BorradoLogico` a propósito: `objects` debe
  seguir siendo un `UserManager` para que funcionen `createsuperuser` y
  `authenticate`.
- `UsuarioManager(UserManager)` adapta la creación al correo
  (`create_user(email, ...)`), porque el `UserManager` de Django exige
  `username`.
- `USERNAME_FIELD = "email"` y `REQUIRED_FIELDS = []`.
- Varios usuarios sin correo conviven en la tabla: en MySQL el índice único deja
  coexistir varios `NULL`. Un usuario sin correo no puede iniciar sesión.

### Matriz de permisos RBAC

Fuente: `apps/common/permisos.py`.

- **`admin` (superadministrador)**: Acceso total de lectura y escritura en todos los módulos (delegaciones, roles, usuarios globales, catálogos, vecinos y atenciones).
- **`delegado`**: Gestión de usuarios acotada a su delegación (`campo_delegacion = "delegacion"`), consulta de vecinos y creación/gestión de atenciones en su territorio. Sin acceso a delegaciones globales ni roles.
- **`funcionario`**: Consulta de lista de vecinos con su historial de atenciones y registro/creación de atenciones en terreno. Sin acceso a gestión de usuarios ni delegaciones.
- **`consulta` / `verificador`**: Lectura restringida de auditoría y catálogos.

### El código visible (`referencia`)

Fuente: `apps/common/referencia.py`.

En un registro conviven tres identificadores y conviene no confundirlos:

- **`id`**: la clave primaria. Interna: no se muestra ni se escribe.
- **`codigo`**: la llave técnica del cargador de datos (`datos_nuevos/`) y de los
  buscadores. No es un identificador visible.
- **`referencia`**: el código que ve el usuario. Es el que aparece en la primera
  columna de cada mantenedor y en la ficha de consulta.

El mixin `ConReferencia` aporta el campo y lo llena solo: se deriva de la clave
primaria en el primer guardado, así que es único por construcción, **inmutable**
(el `pk` nunca cambia) y no tiene condición de carrera entre procesos. También
es buscable: `referencia` está en la tupla `busqueda` de cada listado.

| Entidad | Prefijo | Ejemplo |
|---|---|---|
| `Delegacion` | `DEL` | `DEL-01` |
| `Rol` | `ROL` | `ROL-01` |
| `Usuario` | `USU` | `USU-01` |
| `Meta` | `MET` | `MET-01` |
| `TipoAtencion` | `TIP` | `TIP-01` |
| `SubAtencion` | `SUB` | `SUB-01` |
| `Vecino` | `VEC` | `VEC-01` |
| `Atencion` | `AT` | `AT-01` |

El campo es `editable=False`, así que ningún formulario lo pide, y va como solo
lectura en la API. Las migraciones de cada app agregan la columna y rellenan lo
ya cargado en el mismo archivo.

### Desactivación, visibilidad y reactivación en CRUD

`apps/common/soft_delete.py` y `apps/common/vistas_base.py`. Es la pieza que explica el diseño de ciclo de vida:

- **Desactivación sin pérdida de visibilidad**: Al dar de baja un registro (`BorradoBase`), el sistema cambia su estado a inactivo y registra la marca temporal de baja. Los listados (`ListadoBase`) muestran todos los registros (usando `model.todos.all()`) aplicando la clase visual `.fila-inactiva` (gris atenuado).
- **Validación de dependencias en uso**: Antes de dar de baja o eliminar una entidad (ej. `Delegacion`, `TipoAtencion`, `Rol`), se ejecuta `objeto.esta_en_uso()`. Si tiene usuarios, vecinos, metas o atenciones activas vinculadas, la operación se bloquea y se muestra una alerta SweetAlert2 explicando los motivos.
- **Botón de reactivación**: Cuando un registro está desactivado o inactivo, la tabla ofrece el botón «Reactivar» (`ReactivarBase`, `<pk>/reactivar/`), el cual restaura el registro a estado activo (`estado = 'activo'`, `is_active = True`, `eliminado = None`) previa confirmación SweetAlert2.

`estado` (en `Vecino`) y `eliminado` son cosas distintas: `estado` es el estado
del vecino (Activo/Inactivo); `eliminado` es la fila retirada del sistema.

---

## 5. Migraciones

Un `0001_initial.py` por app con modelos (`panel` no tiene): **seis** en total.
Encima hay migraciones `0002`, `0003` y `0004` que corrigen la forma de los datos
ya cargados o agregan modelos nuevos. Cada uno traduce el modelo a la creación de
su tabla.

Fuente: `apps/*/migrations/0001_initial.py`. Dependencias entre migraciones:

| Migración | Depende de |
|---|---|
| `organizacion.0001_initial` | — |
| `cuentas.0001_initial` | `auth.0012`, `organizacion.0001_initial` |
| `catalogos.0001_initial` | `organizacion.0001_initial` |
| `ciudadanos.0001_initial` | `organizacion.0001_initial` |

`cuentas` depende de `auth` porque `Usuario` hereda de `AbstractUser`. El orden
importa: `Delegacion` debe existir antes que las tablas que la referencian.

Comandos:

```bash
python manage.py makemigrations   # modelos → archivos de migración
python manage.py migrate          # archivos de migración → tablas en MariaDB
```

---

## 6. El ORM en acción

El ORM traduce objetos Python a SQL. Ejemplos tomados de los listados
(`apps/common/vistas_base.py`) y del comando de carga
(`apps/panel/management/commands/cargar_datos.py`).

```python
# Listado por gestor: objects ya excluye los eliminados (ActivosManager).
queryset = super().get_queryset()

# JOIN para las llaves foráneas que la plantilla recorre (evita N+1 consultas).
queryset = queryset.select_related("territorio")

# Búsqueda: un OR sobre varios campos con icontains.
condicion = Q()
for campo in ("nombre", "rut", "territorio__nombre"):
    condicion |= Q(**{f"{campo}__icontains": q})
queryset = queryset.filter(condicion)

# Alta/actualización idempotente (usada por cargar_datos).
modelo.todos.update_or_create(codigo=fila["codigo"], defaults=valores)

# Escritura por atributo: el objeto se edita y se guarda.
usuario.set_password(clave)
usuario.save()

# Borrado lógico: en vez de DELETE, se marca la fila.
self.object.eliminar()
```

---

## 7. Rutas (URLs)

Raíz: `config/urls.py`.

```python
urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/v1/", include("apps.api.urls")),
    path("", include("apps.cuentas.urls")),
    path("", include("apps.panel.urls")),
    path("", include("apps.organizacion.urls")),
    path("", include("apps.catalogos.urls")),
    path("", include("apps.ciudadanos.urls")),
    path("", include("apps.atenciones.urls")),
]
```

Cada app define su `app_name` (namespace). Cada mantenedor expone cinco rutas:
listado, alta, consulta, edición y borrado. Fuente: `apps/*/urls.py`.

| Namespace | Rutas |
|---|---|
| `panel` | `` → Inicio, `contexto/delegacion/` (cambiar delegación activa) |
| `organizacion` | `delegaciones/`, `.../nueva/`, `.../<pk>/`, `.../<pk>/editar/`, `.../<pk>/eliminar/` |
| `cuentas` | `roles/...`, `usuarios/...`, `login/`, `logout/`, `recuperar/`, `validar/`, `reenviar/`, `nueva-password/` |
| `catalogos` | `metas/...`, `tipos-atencion/...`, `sub-atenciones/...` |
| `ciudadanos` | `vecinos/...` |
| `atenciones` | `atenciones/`, `atenciones/crear/`, `.../<pk>/`, `.../<pk>/editar/`, `.../<pk>/eliminar/` |

---

## 8. Vistas

Las vistas se apoyan en un tronco compartido, `apps/common/vistas_base.py`, para
no repetir el CRUD siete veces.

- `Comun`: mixin con los datos que cada módulo declara (`titulo`, `subtitulo`,
  `seccion`, `etiqueta_nueva`, `url_listado`, `url_nueva`) y los inyecta al
  contexto.
- `ListadoBase(Comun, LoginRequiredMixin, ListView)`: plantilla `listado.html`;
  `busqueda` (tupla de campos) arma el `OR` con `icontains`; `relacionadas`
  aplica `select_related`.
- `AltaBase(CreateView)` y `EdicionBase(UpdateView)`, ambos sobre
  `_FormularioBase` (plantilla `formulario.html`; con `X-Modal: 1` devuelve
  `modal/formulario.html`).
- `BorradoBase(Comun, LoginRequiredMixin, DeleteView)`: plantilla `confirmar.html`;
  su `form_valid` llama a `self.object.eliminar()` en vez de borrar.

Cada mantenedor declara solo sus datos. Ejemplo real
(`apps/ciudadanos/views.py`):

```python
class Listado(ListadoBase):
    model = Vecino
    template_name = "ciudadanos/vecinos_lista.html"
    titulo = "Vecinos"
    seccion = "vecinos"
    etiqueta_nueva = "Nuevo vecino"
    busqueda = ("nombre", "rut", "direccion", "telefono", "territorio__nombre", "tipo_gestion")
    relacionadas = ("territorio",)
    url_nueva = "ciudadanos:vecinos_nueva"
    url_listado = "ciudadanos:vecinos"
```

Nota de implementación: `Usuario` conserva el `UserManager` (no filtra por
borrado lógico), así que `UsuariosListado.get_queryset()` filtra a mano con
`.filter(eliminado__isnull=True)`. Lo mismo hace `UsuarioAdmin.get_queryset`.

Las pantallas de autenticación son `FormView`/`View` en
`apps/cuentas/views.py` (ver §10).

---

## 9. Formularios

`apps/*/forms.py`.

- `DelegacionForm`, `MetaForm`, `TipoAtencionForm`, `SubAtencionForm`,
  `VecinoForm`, `RolForm`: `ModelForm` con la lista de `fields` igual a las
  columnas editables del modelo.
- `UsuarioForm`: el mantenedor propio de usuarios. El correo es obligatorio al
  crear (es el camino de activación) y editable al editar; `clean_email` lo
  guarda como `None` si queda vacío, no como cadena vacía, para no chocar con el
  índice único. Recibe `nombre` y `apellido`; **no** pide contraseña. Al crear,
  `save()` deja la cuenta `is_active=False` con `set_unusable_password()` y el
  correo de activación se manda desde la vista. `delegaciones_autorizadas` es el
  M2M que el selector de contexto ofrece.
- `FormularioLogin(AuthenticationForm)`: solo reetiqueta el campo interno
  `username` como "Correo electrónico" (porque `USERNAME_FIELD` es el correo).
- Formularios del flujo OTP: `RecuperarForm`, `CodigoForm` (valida 6 dígitos) y
  `NuevaPasswordForm` (confirma y aplica `validate_password`).

---

## 10. Autenticación

Fuente: `config/settings.py`, `apps/cuentas/views.py`, `apps/cuentas/validators.py`.

Configuración:

```python
LOGIN_URL = "cuentas:login"
LOGIN_REDIRECT_URL = "panel:inicio"
LOGOUT_REDIRECT_URL = "cuentas:login"
OTP_EXPIRY_MINUTES = 10
```

Validadores de contraseña activos: `UserAttributeSimilarityValidator`,
`MinimumLengthValidator` (`PASSWORD_MIN_LENGTH`, por defecto 8),
`CommonPasswordValidator`, `NumericPasswordValidator` y
`RequisitosInstitucionalesValidator` (exige mayúscula, minúscula y un carácter
especial).

Flujo de recuperación en cuatro pasos (`apps/cuentas/views.py`):

1. **Recuperar** (`FormView`): busca el usuario por correo; si existe, genera el
   código y lo envía. La respuesta es la misma exista o no el correo, para no
   revelar qué cuentas hay.
2. **Validar** (`FormView`): si no hay código en sesión, redirige a recuperar.
   Comprueba expiración y coincidencia; al acertar borra el código de la sesión
   (sirve una sola vez) y marca `otp_validado`.
3. **Reenviar** (`View`, POST): genera un código nuevo.
4. **NuevaPassword** (`FormView`): exige `otp_validado`; cambia la contraseña con
   `set_password` y limpia la sesión.

Detalle de implementación del OTP (`apps/cuentas/otp.py`): el código se genera
con `secrets.randbelow(1000000)` formateado a 6 dígitos y vive en la tabla
`RecuperacionPassword`, con vencimiento de `OTP_EXPIRY_MINUTES` y tope de cinco
intentos. El correo sale de las plantillas `correo/recuperacion.txt` y
`correo/recuperacion.html`, que viajan juntas en un mismo mensaje
(`send_mail(html_message=...)`). Al pedir el código la cuenta queda deshabilitada
y se reactiva cuando se guarda la contraseña nueva.

### 10.1 Alta de usuarios por invitación

Fuente: `apps/cuentas/invitaciones.py`, `apps/cuentas/views.py`.

- El administrador **no define** la contraseña. Al crear una cuenta, el
  mantenedor la deja **pendiente** (`is_active=False`, sin contraseña usable) y
  le envía un enlace firmado al correo (`correo/invitacion.*`).
- El enlace (`/activar/<uidb64>/<token>/`) usa el `default_token_generator` de
  Django: el token se firma con la contraseña actual del usuario, así que al
  guardarla **deja de valer** (sirve una sola vez) y vence en `INVITACION_DIAS`
  (`PASSWORD_RESET_TIMEOUT`). Un enlace vencido o ya usado muestra el aviso de
  inválido.
- La vista `Activar` reutiliza `NuevaPasswordForm`: valida la clave, la guarda y
  pone `is_active=True`. Desde ahí la persona inicia sesión normalmente.
- Como el administrador no puede fijar la clave, el listado de Usuarios ofrece
  **reenviar la invitación** a las cuentas pendientes, y muestra el estado
  `Pendiente` (`Usuario.estado_texto`).

---

## 11. Django Admin

Fuente: `apps/common/admin_base.py` y los `admin.py` de cada app.

- `AdminBase(admin.ModelAdmin)`: base común con `list_per_page = 25`. El Admin
  usa el **borrado normal** de Django (emite `DELETE`), a diferencia del front,
  que usa borrado lógico. Como las llaves foráneas están en `PROTECT`, intentar
  borrar una fila que otra referencia muestra un error en vez de arrastrar a las
  dependientes.

Las 7 entidades están registradas, con `list_display`, `search_fields` y
`list_filter`:

| Admin | Registra | Notas |
|---|---|---|
| `RolAdmin` | `Rol` | busca por nombre y descripción |
| `UsuarioAdmin` | `Usuario` | hereda de `BaseUserAdmin`; formularios propios de alta y edición; `autocomplete_fields = ("rol", "delegacion")`; oculta los eliminados |
| `DelegacionAdmin` | `Delegacion` | filtro por comuna |
| `MetaAdmin` | `Meta` | `autocomplete` de delegación |
| `TipoAtencionAdmin` | `TipoAtencion` | — |
| `SubAtencionAdmin` | `SubAtencion` | filtro por tipo de atención |
| `VecinoAdmin` | `Vecino` | filtros por territorio y estado |

`UsuarioAdmin` usa dos formularios propios (definidos en `apps/cuentas/admin.py`):
`UsuarioCrearForm` (basado en `BaseUserCreationForm`) y `UsuarioEditarForm`
(basado en `UserChangeForm`). Ambos comparten el mixin `CorreoNulo`, que guarda
el correo vacío como `NULL`.

---

## 12. Carga de datos

### 12.1 Los JSON

Viven en `datos_nuevos/`, un archivo por entidad, con un arreglo de objetos cuyas
claves coinciden con los campos del modelo.

| Archivo | Filas |
|---|---|
| `delegaciones.json` | 6 |
| `roles.json` | 6 |
| `usuarios.json` | 6 |
| `metas.json` | 6 |
| `tipos_atencion.json` | 4 |
| `sub_atenciones.json` | 8 |
| `vecinos.json` | 10 |
| **Total** | **46** |

### 12.2 El comando `cargar_datos`

Fuente: `apps/panel/management/commands/cargar_datos.py`.

- Lee cada archivo con `json.load` desde `settings.BASE_DIR / "datos_nuevos"`.
- Escribe con `update_or_create`, así que **es idempotente**: correrlo dos veces
  deja los mismos conteos y no duplica.
- Usa el gestor `todos` y limpia `eliminado = None`: recargar el JSON **restaura**
  lo que estaba dado de baja.
- Todo el `handle` corre dentro de `@transaction.atomic`.
- Recorre las entidades en orden de dependencia: delegaciones y roles → usuarios
  → metas, tipos y sub atenciones → vecinos.
- Informa `N creados, M actualizados`.

El caso de `Usuario` es propio (`cargar_usuarios`): la llave de idempotencia es
el nombre y apellido (no el correo, que puede ser nulo), y a cada usuario creado
se le aplica `set_password(settings.USUARIOS_PASSWORD_INICIAL)` solo si tiene
correo (sin correo la contraseña queda inutilizable).

Ejecución:

```bash
python manage.py cargar_datos
# Listo: 46 creados, 0 actualizados.
```

### 12.3 Por qué un comando y no `loaddata`

`loaddata` (fixtures de Django) no transforma datos, no respeta orden de
dependencias por sí solo y no hashea contraseñas. El comando propio existe para
cubrir esas tres cosas y mantener la carga idempotente.

### 12.4 Vecinos de relleno

`apps/ciudadanos/management/commands/generar_vecinos.py`.

- Genera vecinos de relleno para volumen de pruebas:
  `python manage.py generar_vecinos --cantidad 1000`.
- Los RUT son **válidos** (dígito verificador módulo 11, con
  `apps.common.validators.digito_verificador`) y únicos; el rango de cuerpos
  (20–30 millones) no choca con los datos de ejemplo.
- Un generador con **semilla fija** produce los mismos datos: reejecutar
  encuentra los RUT ya creados y no agrega ni cambia nada.

---

## 13. Front-end

### 13.1 Plantillas

Fuente: `templates/`.

- `base.html`: armazón con sidebar (Inicio + grupo "Mantenedores" con los 7
  ítems), header con el usuario y su menú. El menú del usuario se resuelve sin
  JavaScript, con `<details>`. El cierre de sesión va por `POST` (Django 5+).
  Marca el ítem activo comparando la variable `seccion`.
- `listado.html`: el patrón de los 7 mantenedores. Cabecera con título y botón
  "+ Nuevo"; buscador; tabla; contador. Define los bloques `encabezado` y `fila`
  que cada lista concreta sobrescribe.
- `formulario.html`: página completa del formulario, respaldo sin JavaScript;
  incluye `partials/formulario.html`.
- `partials/formulario.html`: render de un `ModelForm` campo por campo, con
  ayuda y errores, y botonera Guardar / Cancelar. Lo comparten la página y el modal.
- `modal/formulario.html`: fragmento que la vista devuelve cuando la petición
  trae `X-Modal: 1`; se inyecta en el `<dialog>` de `base.html`.
- `partials/crear_atencion.html` + `modal/crear_atencion.html`: el flujo de
  Crear Atención (buscar vecino, historial, formulario), en página y en modal.
- `iconos/*.html`: iconos SVG (nuevo, exportar, editar, eliminar, guardar,
  cancelar, cerrar, anterior, siguiente, buscar).
- `confirmar.html`: confirmación de baja lógica ("¿Confirmas dar de baja …?").
- `inicio.html`: página de bienvenida.
- `cuentas/base_auth.html` + `login.html`, `recuperar.html`, `validar.html`,
  `nueva_password.html`: las pantallas de acceso.
- Una lista por entidad en `templates/<app>/…_lista.html`, todas extendiendo
  `listado.html`.

### 13.2 Estáticos

Fuente: `static/`.

- `css/frameworkV1.css` y `css/institucional.css` (paleta institucional).
- `img/logolaserena.png`.
- `js/busqueda.js`: buscador en vivo. Escucha `input`, aplica un *debounce* de
  250 ms, pide la misma URL del listado con `?q=`, y reemplaza las filas y el
  contador (`[data-filas]`, `[data-pie]`) sin recargar, conservando el foco. Si
  JavaScript falla o no corre, el formulario sigue funcionando con Enter.
- `js/modal.js`: abre el CRUD en el `<dialog>` nativo. Pide el formulario como
  fragmento (`X-Modal: 1`) y lo envía por `fetch`; tras guardar refresca el
  listado sin recargar. Sin JavaScript, los enlaces abren las páginas completas.
- `js/mensajes.js`: avisos (toast) y confirmación de baja con SweetAlert2. Los
  eventos van por delegación y expone `window.Mensajes.avisar` para el modal.

---

## 14. Variables de entorno

Fuente: `.env.example` y `config/settings.py`. La configuración se lee con
`python-dotenv`; no hay credenciales en el código.

```text
# Django
SECRET_KEY=
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# Base de datos MariaDB
DB_NAME=abstergo
DB_USER=abstergo
DB_PASSWORD=
DB_HOST=127.0.0.1
DB_PORT=3306

# Localización
LANGUAGE_CODE=es
TIME_ZONE=America/Santiago

# Correo
MAILER_BACKEND=django.core.mail.backends.console.EmailBackend
EMAIL_HOST=
EMAIL_PORT=587
EMAIL_HOST_USER=
EMAIL_HOST_PASSWORD=
EMAIL_USE_TLS=True
DEFAULT_FROM_EMAIL=no-reply@muniserena.cl

# Autenticación
OTP_EXPIRY_MINUTES=10
PASSWORD_MIN_LENGTH=8
USUARIOS_PASSWORD_INICIAL=

# API (cliente móvil)
JWT_ACCESS_MINUTES=60
JWT_REFRESH_DAYS=7
API_PAGE_SIZE=20
```

En `settings.py`, el backend de correo se declara en `MAILERS` (reemplaza a
`EMAIL_BACKEND` en Django 6): en desarrollo usa la consola y en el servidor el
backend SMTP, cuyas `OPTIONS` solo se añaden cuando corresponde.

El `.gitignore` deja fuera `venv/`, `.env*` (salvo `.env.example`), llaves
`*.pem`/`*.key`, `__pycache__/`, `*.sqlite3`, `staticfiles/` y `media/`.

---

## 15. Puesta en marcha

Fuente: `README.md`.

1. Requisitos del sistema: MariaDB y sus librerías de desarrollo (el orden
   importa, porque `mysqlclient` compila contra sus headers).

   ```bash
   sudo pacman -S mariadb        # o el gestor de paquetes de tu distro
   ```

2. Entorno virtual y dependencias:

   ```bash
   python -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   pip install mysqlclient        # después de instalar MariaDB
   ```

3. Variables de entorno: copiar `.env.example` a `.env` y completarlo.

4. Base de datos y datos:

   ```bash
   python manage.py migrate
   python manage.py cargar_datos   # lee datos_nuevos/; reejecutable sin duplicar
   python manage.py runserver
   ```

En producción, el servidor WSGI es `gunicorn` (`gunicorn` está en
`requirements.txt`) y los estáticos se sirven desde `STATIC_ROOT`
(`staticfiles/`, poblado con `collectstatic`).

---

## 16. Mapa de archivos citado

| Archivo | Contenido |
|---|---|
| `manage.py` | Entrada de los comandos de Django |
| `config/settings.py` | Configuración desde `.env`, apps, BD, correo, auth |
| `config/urls.py` | Rutas raíz |
| `apps/common/soft_delete.py` | `Eliminado`, `BorradoLogico`, gestores |
| `apps/common/admin_base.py` | `AdminBase` (CRUD; borrado normal en el Admin) |
| `apps/common/vistas_base.py` | Tronco de las vistas CRUD |
| `apps/cuentas/models.py` | `Rol`, `Usuario`, `UsuarioManager` |
| `apps/cuentas/views.py` | Mantenedores + flujo OTP |
| `apps/cuentas/forms.py` | Formularios de login, mantenedor y OTP |
| `apps/cuentas/validators.py` | `RequisitosInstitucionalesValidator` |
| `apps/cuentas/admin.py` | `RolAdmin`, `UsuarioAdmin` |
| `apps/organizacion/models.py` | `Delegacion` |
| `apps/catalogos/models.py` | `Meta`, `TipoAtencion`, `SubAtencion` |
| `apps/ciudadanos/models.py` | `Vecino` |
| `apps/panel/management/commands/cargar_datos.py` | Comando de carga |
| `datos_nuevos/*.json` | Datos de importación (46 filas) |
| `templates/` | Armazón, listados, formularios y acceso |
| `static/js/busqueda.js` | Buscador en vivo |

---

## 17. Modelo v2 y Ley 21.719 (implementado)

Describe piezas del proyecto ya implementadas; el diseño original vive en
`documentacion/vision.md`.

Tablas nuevas:

- `Atencion`: vecino, tipo y sub atención, delegación, funcionario, fecha,
  motivo, detalle, estado y canal. El historial de un vecino es la consulta de sus
  atenciones.
- `Delegacion.responsable`: FK a `Usuario`, un solo delegado.
- `ActividadTratamiento`: registro de actividades (finalidad, base de licitud,
  plazo de conservación).
- `SolicitudTitular`: derechos ARCOP más bloqueo, con plazo de 30 días.
- `IncidenteSeguridad`: vulneraciones y su notificación.
- `RegistroAuditoria`: accesos y cambios.
- `Consentimiento`: solo si un tratamiento se funda en consentimiento.

Reglas transversales, definidas una sola vez en `apps/common`:

- Validación por expresión regular, con el RUT validado por dígito verificador.
- Confirmación y avisos con SweetAlert.
- Alta y edición del CRUD en modal (`<dialog>`), con botones de icono SVG.
- Listados con paginación de 7 filas.
- Exportación a `.xlsx` con `openpyxl`, respetando el filtro y todas las páginas.

---

## 18. API y permisos (implementado)

Fuente: `apps/api/`, `apps/common/permisos.py`, `config/urls.py`.

### 18.1 API v1

- Base `/api/v1/` con el router de DRF. Esquema OpenAPI en `/api/schema/` y
  documentación navegable en `/api/docs/`.
- Autenticación con JWT (`djangorestframework-simplejwt`): `POST /api/v1/auth/login/`
  devuelve `access` y `refresh`; `.../refresh/` renueva; `.../logout/` invalida el
  refresh (blacklist); `GET .../me/` devuelve el usuario.
- Recuperación de contraseña: `.../recuperar/`, `.../validar/` y
  `.../nueva-password/`. El código de 6 dígitos vive en
  `cuentas.RecuperacionPassword` (no en la sesión), con vencimiento, tope de 5
  intentos y comparación en tiempo constante. Pedir recuperación **no** desactiva
  la cuenta.
- CRUD: un viewset por entidad (`roles`, `usuarios`, `delegaciones`, `metas`,
  `tipos-atencion`, `sub-atenciones`, `vecinos`, `atenciones`), con borrado lógico.

### 18.2 Permisos por rol

- La política vive una sola vez en `apps/common/permisos.py`: una matriz
  `módulo → {lectura, escritura}` sobre los códigos de `Rol.codigo`. Cambiarla es
  editar ese archivo.
- La web la aplica con `PermisoRequeridoMixin`: el anónimo va al login y el
  autenticado sin permiso recibe 403.
- La API la aplica con `PermisoPorRol`, que lee el atributo `modulo` de cada
  viewset.
- La barra lateral muestra solo los módulos con lectura permitida, vía el context
  processor `apps.common.contexto.permisos`.
- El superusuario cuenta como `admin`.

### 18.3 El contrato está en inglés

Adentro el dominio está en español y los modelos no se tocan; lo que sale por la
API está en inglés, con `source` en cada campo del serializer. Este es el
glosario, el mismo que usa el cliente Android:

- `Rol` → `role`: `codigo` → `code`, `nombre` → `name`, `descripcion` → `description`.
- `referencia` → `reference_code` en **todas** las entidades: es el código visible
  (`DEL-01`, `AT-01`…) y viaja como solo lectura, porque lo genera el servidor.
- `Usuario` → `user`: `rol` → `role`, `delegacion` → `delegation`.
- `Delegacion` → `delegation`: `codigo` → `code`, `nombre` → `name`,
  `direccion` → `address`, `comuna` → `commune`, `responsable` → `manager`.
- `Meta` → `goal`: `nombre` → `name`, `descripcion` → `description`,
  `delegacion` → `delegation`.
- `TipoAtencion` → `attention_type`: `nombre` → `name`, `descripcion` → `description`.
- `SubAtencion` → `attention_subtype`: `nombre` → `name`,
  `tipo_atencion` → `attention_type`.
- `Vecino` → `neighbor`: `nombre` → `name`, `rut` se mantiene,
  `direccion` → `address`, `telefono` → `phone`, `territorio` → `territory`,
  `tipo_gestion` → `management_type`, `estado` → `status`.
- `Atencion` → `case`: `vecino` → `neighbor`, `tipo_atencion` → `attention_type`,
  `sub_atencion` → `attention_subtype`, `delegacion` → `delegation`,
  `funcionario` → `staff`, `fecha` → `date`, `motivo` → `reason`,
  `detalle` → `detail`, `estado` → `status`, `canal` → `channel`.
- `Perfil` → `profile`: `rol_codigo` → `role_code`,
  `modulos_lectura` → `read_modules`, `modulos_escritura` → `write_modules`.
- En la recuperación, `codigo` → `code`. `email`, `password`, `refresh` y
  `detail` se mantienen.
- Rutas: `auth/recover/`, `auth/verify/`, `auth/new-password/`; y los recursos
  `roles`, `users`, `delegations`, `goals`, `attention-types`,
  `attention-subtypes`, `neighbors`, `cases`.
- Las claves de módulo de la matriz (§18.2) viajan en `read_modules` y
  `write_modules`, así que también están en inglés.

---

## 19. Contexto de delegación, consulta y pruebas (implementado)

Piezas que cierran los requisitos de la segunda evaluación.

### 19.1 Contexto de delegación

Fuente: `apps/common/delegaciones.py`, `apps/common/contexto.py`,
`apps/panel/views.py`, `templates/base.html`.

- Cada usuario tiene una delegación **principal** (`Usuario.delegacion`) y, si
  su perfil trabaja en más de un territorio, un conjunto de **autorizadas**
  (`Usuario.delegaciones_autorizadas`, M2M).
- La **delegación activa** se guarda en la sesión (`delegacion_activa`) y se
  valida contra las autorizadas: una delegación no autorizada nunca se activa.
- Los roles de **alcance global** (admin y coordinador) ven todas las
  delegaciones; su delegación activa es "todas" salvo que elijan una.
- La **cabecera** muestra de forma permanente el código y el nombre de la
  delegación activa, más el usuario y su rol, con icono y texto (el color no es
  la única señal). Cuando el perfil tiene más de una, aparece el **selector**,
  que recarga el contexto en el servidor.
- `ListadoBase.campo_delegacion` acota el queryset del listado —y por ende la
  exportación— a la delegación activa. El mismo queryset alimenta el `.xlsx`.
- Los formularios (`apps/common/forms.py`) acotan sus campos de delegación a las
  autorizadas, así el servidor rechaza una delegación ajena aunque se altere la
  petición.

### 19.2 Vista de consulta

- `ConsultaBase` (`apps/common/vistas_base.py`) agrega la ficha de solo lectura
  que completa el CRUD (crear, **consultar**, listar, editar, eliminar).
- Cada módulo declara `consulta_campos`; la plantilla los renderiza igual en la
  página completa (`templates/consulta.html`) y en el modal
  (`templates/modal/consulta.html`).
- `resolver_campo` comparte con la exportación la forma de leer un campo.

### 19.3 Reglas de la segunda entrega

- **Estado y código**: `ConEstado` y el campo `codigo` en los catálogos.
- **Tipo → Sub Atención**: `SelectSubAtencion` marca cada opción con su tipo; el
  JavaScript (`static/js/atencion.js`) muestra solo las del tipo elegido y
  limpia la que deja de ser válida; `AtencionForm.clean` valida lo mismo en el
  servidor. El ingreso de atención muestra el **identificador** y deriva la
  delegación del contexto autorizado.
- **Estados de interfaz**: los listados distinguen "sin coincidencias" de
  "aún no hay registros", muestran el estado de carga y avisan el error de red.
- **Reenvío del código**: `otp.reenviar` respeta la espera mínima
  (`OTP_REENVIO_SEGUNDOS`), además del tope de intentos ya existente.

### 19.4 Pruebas

- Automatizadas con `pytest` (`apps/*/tests.py`, `apps/common/test_web.py`,
  `conftest.py`): permisos, listados, alcance por delegación, búsqueda,
  exportación, consulta, catálogos, ingreso de atención y recuperación.
- El registro de resultados, con evidencias y la prueba de carga, vive en
  `documentacion/pruebas.md`; la carga la corre `scripts/estres.py`.
