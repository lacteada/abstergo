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

- 8 entidades modeladas con el ORM de Django, con llaves foráneas y borrado lógico.
- Carga de datos desde JSON con un comando de management idempotente.
- Django Admin con CRUD completo y borrado lógico.
- Front-end con un listado por entidad, buscador en vivo y CRUD (alta, edición,
  baja).
- Autenticación: login por correo, recuperar contraseña con código OTP de 6
  dígitos o enlace firmado al correo, y cambio de contraseña.

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
| 2 | `Cargo` | organizacion | `organizacion_cargo` | `codigo` (único), `nombre` (único), `descripcion` |
| 3 | `Rol` | cuentas | `cuentas_rol` | `nombre` (único), `descripcion`, `codigo` (único) |
| 4 | `Usuario` | cuentas | `cuentas_usuario` | `email` (único, nulo), `rol`, `cargo`, `delegacion`, `delegaciones_autorizadas` (M2M) + campos de `AbstractUser` |
| 5 | `Meta` | catalogos | `catalogos_meta` | `codigo` (único), `nombre`, `descripcion`, `delegacion`, `estado` |
| 6 | `TipoAtencion` | catalogos | `catalogos_tipoatencion` | `codigo` (único), `nombre`, `descripcion`, `estado` |
| 7 | `SubAtencion` | catalogos | `catalogos_subatencion` | `codigo` (único), `nombre`, `tipo_atencion`, `estado` |
| 8 | `Vecino` | ciudadanos | `ciudadanos_vecino` | `nombre`, `rut` (único), `direccion`, `telefono`, `territorio`, `tipo_gestion`, `estado` |

Toda entidad lleva además la columna `eliminado` (`DateTimeField`, nulo) que
aporta el borrado lógico, y —salvo `Usuario` y `Vecino`, que tienen su propio
`estado`, y `Rol` y `Cargo`, que no lo usan— la columna `estado`
(`Activo`/`Inactivo`) que aporta `ConEstado` (`apps/common/estados.py`).
`estado` es el dato de negocio; `eliminado` es la fila retirada del sistema.

### Relaciones (llaves foráneas)

Todas con `on_delete=models.PROTECT`:

| Desde | Hacia | Nulo | `related_name` |
|---|---|---|---|
| `Usuario.rol` | `Rol` | sí | `usuarios` |
| `Usuario.cargo` | `Cargo` | sí | `usuarios` |
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
- `cargo` (puesto funcional, FK a `Cargo`) y `delegaciones_autorizadas` (M2M).
- `guia_vista` (booleano): la guía de bienvenida se abre la primera vez; queda
  marcada al verla o saltarla y se puede reabrir con `?guia=1` desde el perfil.
- Varios usuarios sin correo conviven en la tabla: en MySQL el índice único deja
  coexistir varios `NULL`. Un usuario sin correo no puede iniciar sesión.

### Matriz de permisos RBAC

Fuente: `apps/common/permisos.py`. La autorización tiene dos ejes: el **rol**
(categoría de acceso al sistema) y el **cargo** (puesto funcional dentro de la
delegación). Un usuario puede tener ambos y el permiso se resuelve por **unión**:
pasa si concede el rol **o** el cargo.

Roles (`Rol.codigo`):

- **`admin` (Administrador)**: acceso total de lectura y escritura en todos los módulos.
- **`coordinador` (Supervisor)**: lee todos los módulos, escribe **solo metas** y ve todas las delegaciones.
- **`delegado` (Administrativo)**: CRUD de atenciones y vecinos en su delegación; lee los catálogos de atención. Sin acceso a usuarios, roles ni delegaciones.
- **`funcionario`**: consulta de vecinos con su historial y registro/creación de atenciones en terreno.
- **`consulta` / `verificador`**: sin permisos operativos por ahora.

Cargos (`Cargo.codigo`, `MATRIZ_CARGO`): suman permisos al rol sobre los
módulos operativos. Los siete cargos del descriptor y sus permisos —casos,
vecinos, metas y catálogos de atención— son una segunda matriz con la misma
forma que la de roles. El detalle de funciones de cada cargo está en
`documentacion/descriptor_cargos_delegaciones.md`. El módulo `positions`
(catálogo de cargos) queda reservado al `admin`.

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
| `Cargo` | `CRG` | `CRG-01` |
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

### Las tres acciones sobre un registro

Fuente: `apps/common/vistas_base.py`. Cada fila del mantenedor ofrece el mismo
juego, y las tres vuelven al listado:

- **Desactivar** (`DesactivarBase`, `<pk>/desactivar/`): saca el registro de
  circulación **sin borrarlo**. Marca `eliminado` y deja el estado en inactivo.
  **Siempre es posible**, aunque el registro esté en uso, y es reversible. La
  fila sigue en el listado en gris (`.fila-inactiva`).
- **Eliminar** (`BorradoBase`, `<pk>/eliminar/`): borra la fila de verdad
  (`delete()`). Es la única acción destructiva. Se bloquea si el registro está
  en uso: primero por negocio (`esta_en_uso()`), que da el mensaje con el
  detalle, y después por la propia base (`ProtectedError`), cuyo error se
  traduce a un aviso entendible en vez de un 500.
- **Reactivar** (`ReactivarBase`, `<pk>/reactivar/`): limpia `eliminado` y
  devuelve el estado a activo.

El cambio de estado binario lo hace `marcar_vigencia(objeto, vigente)`, que solo
toca los modelos cuyo `estado` es el par activo/inactivo (`ConEstado` y
`Vecino`). Una `Atencion` usa `estado` para su ciclo de vida —ingresada,
cerrada…—, así que ahí la vigencia es solo la marca de `eliminado`.

**Visibilidad**: `ListadoBase` lista con `model.todos.all()`, así que lo
desactivado se ve; `objects` (el gestor por defecto) sigue filtrando
`eliminado__isnull=True`, así que no aparece en desplegables ni en referencias
nuevas.

### La clave técnica `codigo`

El mantenedor **no pide** `codigo`: se deriva del nombre al guardar
(`apps/common/codigo.py`, `ConCodigoDerivado`), con el mismo criterio con que
las migraciones rellenaron lo ya cargado. Se ignora si viene indicado, porque
`cargar_datos` lo trae en el JSON y la carga debe seguir siendo idempotente.

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
| `cuentas` | `roles/...`, `usuarios/...`, `login/`, `logout/`, `recuperar/`, `recuperar/<uidb64>/<token>/`, `validar/`, `reenviar/`, `nueva-password/` |
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
OTP_EXPIRY_MINUTES = 5
```

Validadores de contraseña activos: `UserAttributeSimilarityValidator`,
`MinimumLengthValidator` (`PASSWORD_MIN_LENGTH`, por defecto 8),
`CommonPasswordValidator`, `NumericPasswordValidator` y
`RequisitosInstitucionalesValidator` (exige mayúscula, minúscula y un carácter
especial).

Flujo de recuperación (`apps/cuentas/views.py`). El correo lleva **dos** caminos
para el mismo registro: el código de 6 dígitos y un enlace firmado. El primero
que se use anula al otro.

1. **Recuperar** (`FormView`): busca el usuario por correo; si existe, genera un
   registro, envía el código y el enlace, y deshabilita la cuenta. La respuesta
   es la misma exista o no el correo, para no revelar qué cuentas hay.
2. **Validar** (`FormView`): si no hay correo en sesión, redirige a recuperar.
   Comprueba expiración y coincidencia; al acertar marca `validado` (sirve una
   sola vez), y con eso el enlace queda inválido.
3. **Reenviar** (`View`, POST): genera un registro nuevo respetando
   `OTP_REENVIO_SEGUNDOS`. El enlace anterior deja de valer.
4. **NuevaPassword** (`FormView`): exige un código ya validado; cambia la
   contraseña y cierra el registro.
5. **RecuperarEnlace** (`FormView`, `recuperar/<uidb64>/<token>/`): la otra
   puerta. Valida el token del registro, pide la contraseña nueva y al guardarla
   marca el registro como usado, con lo que el código deja de valer. Un enlace
   vencido, ya usado o ya cerrado por el código muestra el aviso de inválido.

Detalle de implementación del OTP (`apps/cuentas/otp.py`): el código se genera
con `secrets.randbelow(1000000)` formateado a 6 dígitos y vive en la tabla
`RecuperacionPassword`, con vencimiento de `OTP_EXPIRY_MINUTES` y tope de cinco
intentos. El enlace firma la clave del registro con `signing` y una sal propia
(`SAL_ENLACE`), así que no vale para la invitación ni para otra recuperación, y
vence con el registro, igual que el código. El correo sale de las plantillas
`correo/recuperacion.txt` y `correo/recuperacion.html`, que viajan juntas en un
mismo mensaje (`send_mail(html_message=...)`). Al pedir el código la cuenta queda
deshabilitada y se reactiva cuando se guarda la contraseña nueva.

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
- No confundir con el enlace de **recuperación** (sección 10): este activa una
  cuenta pendiente y vive días; aquel cierra un `RecuperacionPassword` y vive
  los mismos minutos que el código, con sal propia (`SAL_ENLACE`).
- La vista `Activar` reutiliza `NuevaPasswordForm`: valida la clave, la guarda y
  pone `is_active=True`. Desde ahí la persona inicia sesión normalmente.
- Como el administrador no puede fijar la clave, el listado de Usuarios ofrece
  **reenviar la invitación** a las cuentas pendientes, y muestra el estado
  `Pendiente` (`Usuario.estado_texto`).

### 10.2 Mi perfil y cambio de contraseña

Fuente: `apps/cuentas/views.py` (`MiPerfil`), `templates/cuentas/mi_perfil.html`.

- Se llega desde el menú de usuario del header ("Mi perfil", `/perfil/`).
- Muestra los datos del usuario (nombre, correo, rol, cargo, delegación,
  delegaciones autorizadas, estado) y un par de contadores personales.
- El **cambio de contraseña** usa el `PasswordChangeForm` de Django, que exige
  la **contraseña actual**; al guardar, `update_session_auth_hash` mantiene la
  sesión abierta (no expulsa al usuario).
- Incluye el botón "Ver la guía de nuevo" (`/?guia=1`), que reabre la guía sin
  volver a marcar la bandera.

---

## 11. Django Admin

Fuente: `apps/common/admin_base.py` y los `admin.py` de cada app.

- `AdminBase(admin.ModelAdmin)`: base común con `list_per_page = 25`. El Admin
  usa el **borrado normal** de Django (emite `DELETE`), a diferencia del front,
  que usa borrado lógico. Como las llaves foráneas están en `PROTECT`, intentar
  borrar una fila que otra referencia muestra un error en vez de arrastrar a las
  dependientes.

Las 8 entidades están registradas, con `list_display`, `search_fields` y
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
| `delegaciones.json` | 7 |
| `cargos.json` | 7 |
| `roles.json` | 6 |
| `usuarios.json` | 11 |
| `metas.json` | 6 |
| `tipos_atencion.json` | 6 |
| `sub_atenciones.json` | 15 |
| `vecinos.json` | 10 |
| **Total** | **68** |

### 12.2 El comando `cargar_datos`

Fuente: `apps/panel/management/commands/cargar_datos.py`.

- Lee cada archivo con `json.load` desde `settings.BASE_DIR / "datos_nuevos"`.
- Escribe con `update_or_create`, así que **es idempotente**: correrlo dos veces
  deja los mismos conteos y no duplica.
- Usa el gestor `todos` y limpia `eliminado = None`: recargar el JSON **restaura**
  lo que estaba dado de baja.
- Todo el `handle` corre dentro de `@transaction.atomic`.
- Recorre las entidades en orden de dependencia: delegaciones, cargos y roles →
  usuarios → metas, tipos y sub atenciones → vecinos.
- Al final siembra **volumen demo** (`cargar_volumen`): territorios, más vecinos
  (vía `generar_vecinos`), organizaciones, atenciones, casos, llamadas,
  compromisos, cartas y la matriz SGR (período, áreas, indicadores, metas,
  actividades, evidencias, validaciones, conductas y ausencias), y genera las
  alertas con `generar_alertas`. El volumen se siembra **una sola vez**: si ya
  hay atenciones o gestiones, el paso se omite (no duplica ni borra).
- Informa `N creados, M actualizados`.

El caso de `Usuario` es propio (`cargar_usuarios`): la llave de idempotencia es
el nombre y apellido (no el correo, que puede ser nulo), y a cada usuario creado
se le aplica `set_password(settings.USUARIOS_PASSWORD_INICIAL)` solo si tiene
correo (sin correo la contraseña queda inutilizable). El JSON de usuarios trae
además `cargo` (opcional) y `delegaciones` (autorizadas).

Ejecución:

```bash
python manage.py cargar_datos
# Volumen demo cargado.
# Listo: 68 creados, 0 actualizados.
```

Con las fechas generadas **relativas a hoy**, los tableros muestran datos
"de hoy" y de la semana en curso; volver a correr el comando no altera los
conteos.

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
- `cargar_datos` lo invoca con una cantidad acotada (60) como parte del volumen
  demo; el comando queda disponible para generar más a mano.

---

## 13. Front-end

### 13.1 Plantillas

Fuente: `templates/`.

- `base.html`: armazón con sidebar (Inicio + grupos "Trabajo" y "Mantenedores"
  **plegables** con `<details>`; `js/sidebar.js` recuerda el estado y abre el
  grupo de la sección activa), header con el usuario y su menú. El menú del
  usuario se resuelve sin JavaScript, con `<details>`, e incluye "Mi perfil". El
  cierre de sesión va por `POST` (Django 5+). Marca el ítem activo comparando la
  variable `seccion` (cada vista la declara).
- `listado.html`: el patrón de los listados. Cabecera con título y botón de alta
  (icono + texto); buscador; tabla; contador. Las acciones de fila son chips con
  **icono y etiqueta** (Consultar, Editar, Desactivar/Reactivar, Eliminar).
  Define los bloques `encabezado` y `fila` que cada lista concreta sobrescribe.
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
- `inicio.html`: panel de bienvenida. Tarjetas por rol, botón principal, bloque
  de estado del período SGR (semáforo por área) y últimas atenciones; si
  corresponde, incluye la **guía** (tour por pasos, `js/guia.js`).
- `listado.html`: además del buscador y la exportación, trae el **selector de
  filas por página** ("Mostrar": 8, 16, 32 o 64; `ListadoBase.tamanos_pagina`).
- `cuentas/mi_perfil.html`: perfil del usuario, sus contadores y el cambio de
  contraseña.
- `cuentas/base_auth.html` + `login.html`, `recuperar.html`, `validar.html`,
  `nueva_password.html`, `recuperar_enlace.html`: las pantallas de acceso.
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
- `js/sidebar.js`: pliega/despliega los grupos del menú y recuerda el estado en
  `localStorage`.
- `js/guia.js`: tour de bienvenida por pasos con resaltado; al terminar o saltar
  avisa a `cuentas:guia_vista`.

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
OTP_EXPIRY_MINUTES=5
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
| `apps/organizacion/models.py` | `Delegacion`, `Cargo` |
| `apps/catalogos/models.py` | `Meta`, `TipoAtencion`, `SubAtencion` |
| `apps/ciudadanos/models.py` | `Vecino` |
| `apps/panel/management/commands/cargar_datos.py` | Comando de carga |
| `datos_nuevos/*.json` | Datos de importación (53 filas) |
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
  `.../nueva-password/`. El cliente móvil usa el código de 6 dígitos; el enlace
  del correo es la vía de la web. El registro vive en
  `cuentas.RecuperacionPassword` (no en la sesión), con vencimiento, tope de 5
  intentos y comparación en tiempo constante. Pedir recuperación deshabilita la
  cuenta hasta que se guarde la contraseña nueva.
- CRUD: un viewset por entidad (`roles`, `positions`, `usuarios`, `delegaciones`,
  `metas`, `tipos-atencion`, `sub-atenciones`, `vecinos`, `atenciones`), con
  borrado lógico. Desde 2026 suma los recursos de los módulos nuevos:
  `community-organizations`, `territories`, `sgr-periods`, `sgr-areas`,
  `sgr-indicators`, `sgr-targets`, `sgr-records`, `sgr-conducts`,
  `sgr-absences`, `tasks`, `evidence`, `validations`, `social-cases`,
  `comments` y `alerts`.

### 18.2 Permisos por rol y cargo

- La política vive una sola vez en `apps/common/permisos.py`: la matriz
  `módulo → {lectura, escritura}` sobre los códigos de `Rol.codigo` y la
  `MATRIZ_CARGO` con la misma forma sobre los códigos de `Cargo.codigo`.
  Cambiarla es editar ese archivo.
- El permiso se resuelve por **unión**: `puede()` concede si el rol **o** el
  cargo autoriza; `modulos_de()` une los módulos de ambos.
- La web la aplica con `PermisoRequeridoMixin`: el anónimo va al login y el
  autenticado sin permiso recibe 403.
- La API la aplica con `PermisoPorRol`, que lee el atributo `modulo` de cada
  viewset.
- La barra lateral muestra solo los módulos con lectura permitida, vía el context
  processor `apps.common.contexto.permisos`; y cada listado oculta los botones de
  CRUD (nuevo, editar, eliminar, desactivar) cuando el perfil no escribe ese
  módulo (`puede_escribir`).
- El superusuario cuenta como `admin`.
- **Grupos espejo**: cada `Rol` se refleja como un `auth.Group` con los permisos
  de Django correspondientes (`apps/cuentas/grupos.py`, señales en
  `apps/cuentas/signals.py`). Es solo un espejo para cumplir y demostrar
  "permisos y grupos": la autorización real sigue siendo la matriz.

### 18.3 El contrato está en inglés

Adentro el dominio está en español y los modelos no se tocan; lo que sale por la
API está en inglés, con `source` en cada campo del serializer. Este es el
glosario, el mismo que usa el cliente Android:

- `Rol` → `role`: `codigo` → `code`, `nombre` → `name`, `descripcion` → `description`.
- `Cargo` → `position`: `codigo` → `code`, `nombre` → `name`,
  `descripcion` → `description`, `funciones` → `functions`.
- `referencia` → `reference_code` en **todas** las entidades: es el código visible
  (`DEL-01`, `AT-01`…) y viaja como solo lectura, porque lo genera el servidor.
- `Usuario` → `user`: `rol` → `role`, `cargo` → `position`,
  `delegacion` → `delegation`.
- `Delegacion` → `delegation`: `codigo` → `code`, `nombre` → `name`,
  `direccion` → `address`, `comuna` → `commune`, `responsable` → `manager`.
- `Meta` → `goal`: `nombre` → `name`, `descripcion` → `description`,
  `delegacion` → `delegation`.
- `TipoAtencion` → `attention_type`: `nombre` → `name`, `descripcion` → `description`.
- `SubAtencion` → `attention_subtype`: `nombre` → `name`,
  `tipo_atencion` → `attention_type`, `forma` → `form`.
- `Vecino` → `neighbor`: `nombre` → `name`, `rut` se mantiene,
  `direccion` → `address`, `telefono` → `phone`, `territorio` → `territory`,
  `tipo_gestion` → `management_type`, `estado` → `status`.
- `Atencion` → `case`: `vecino` → `neighbor`, `tipo_atencion` → `attention_type`,
  `sub_atencion` → `attention_subtype`, `delegacion` → `delegation`,
  `funcionario` → `staff`, `fecha` → `date`, `motivo` → `reason`,
  `detalle` → `detail`, `estado` → `status`, `canal` → `channel`.
- `Organizacion` → `community_organization`: `nombre` → `name`,
  `domicilio_legal` → `legal_address`, `territorio` → `territory`,
  `tipo` → `organization_type`, `subtipo` → `subtype`, `situacion` → `situation`,
  `verificacion` → `verification`, `socios_activos` → `active_members`,
  `fecha_constitucion` → `constitution_date`, `registro_pj` → `pj_registry`,
  `fecha_inscripcion` → `registration_date`, `registro_dir` → `directive_registry`,
  `estado` → `status`.
- `Territorio` → `territory`: `nombre` → `name`, `delegacion` → `delegation`,
  `estado` → `status`.
- `Periodo` → `sgr_period`: `nombre` → `name`, `inicio` → `start`,
  `termino` → `end`, `dias` → `days`, `situacion` → `situation`,
  `umbral_minimo` → `min_threshold`, `umbral_ambar` → `amber_threshold`,
  `tope_item` → `item_cap`, `tope_total` → `total_cap`, `estado` → `status`.
- `Area` → `sgr_area`: `nombre` → `name`, `grupo` → `group`, `cargo` → `position`,
  `responsable` → `manager`, `delegacion` → `delegation`, `estado` → `status`.
- `Indicador` → `sgr_indicator`: `nombre` → `name`, `grupo` → `group`,
  `unidad` → `unit`, `cargo` → `position`, `tipo_calculo` → `calculation_type`,
  `requiere_evidencia` → `requires_evidence`, `estado` → `status`.
- `MetaIndicador` → `sgr_target`: `periodo` → `period`, `area` se mantiene,
  `indicador` → `indicator`, `ponderador` → `weight`, `meta` → `target`,
  `funcionario` → `staff`, `vigente_desde` → `effective_from`.
- `RegistroGestion` (la actividad) → `sgr_record`: `fecha` → `date`,
  `area` se mantiene, `indicador` → `indicator`, `vecino` → `neighbor`,
  `compromiso` → `commitment`, `funcionario` → `staff`, `cantidad` → `quantity`,
  `detalle` → `detail`, `etapa` → `stage`, `tipo_solicitante` → `requester_type`,
  `contacto_nombre` → `contact_name`, `contacto_telefono` → `contact_phone`,
  `puntua` → `scores`, `motivo_no_puntua` → `no_score_reason`,
  `estado` → `status`, `accion` → `action`, `actividad` → `activity`,
  `organizacion` → `organization`, `version` se mantiene. Además, en la
  **creación** acepta la evidencia adjunta (solo escritura): `evidencia_archivo`
  → `evidence_file`, `evidencia_vinculo` → `evidence_link`,
  `evidencia_tipo` → `evidence_kind`.
- `AjusteConducta` → `sgr_conduct`: `area` se mantiene, `tipo` → `kind`,
  `fecha` → `date`, `respaldo` → `backing`, `medio` → `medium`, `valor` → `value`,
  `periodo` → `period`.
- `Ausencia` → `absence`: `area` se mantiene, `periodo` → `period`,
  `tipo` → `kind`, `desde` → `start`, `hasta` → `end`, `dias` → `days`.
- `Evidencia` → `evidence`: `registro` → `record`, `archivo` → `file`,
  `vinculo` → `link`, `autor` → `author`, `tipo` → `kind`,
  `estado_revision` → `review_status`.
- `Validacion` → `validation`: `evidencia` → `evidence`,
  `verificador` → `reviewer`, `decision` se mantiene, `observacion` → `observation`.
- `TareaTubo` (el compromiso) → `task`: `titulo` → `title`,
  `descripcion` → `description`, `estado` → `status`, `delegacion` → `delegation`,
  `territorio` → `territory`, `tipo` → `kind`, `solicitante` → `requester`,
  `responsable` → `assignee`, `apoyo` → `support`, `vecino` → `neighbor`,
  `atencion` → `attention`, `avance` → `progress`, `vencida` → `overdue`,
  `fecha_ingreso` → `created_at`, `fecha_compromiso` → `due_date`.
- `CasoSocial` → `social_case`: `vecino` → `neighbor`, `responsable` → `manager`,
  `fecha_apertura` → `opened_at`, `motivo` → `reason`, `estado` → `status`,
  `reingreso` → `is_reentry`, `caso_anterior` → `previous_case`,
  `observaciones` → `notes`.
- `Comentario` → `comment`: `registro` → `record`, `autor` → `author`,
  `texto` → `text`, `fecha` → `date`.
- `Alerta` → `alert`: `tipo` → `kind`, `severidad` → `severity`,
  `mensaje` → `message`, `resuelta` → `solved`, `fecha` → `date`.
- `Perfil` → `profile`: `rol_codigo` → `role_code`,
  `cargo_codigo` → `position_code`, `modulos_lectura` → `read_modules`,
  `modulos_escritura` → `write_modules`.
- En la recuperación, `codigo` → `code`. `email`, `password`, `refresh` y
  `detail` se mantienen.
- Rutas: `auth/recover/`, `auth/verify/`, `auth/new-password/`; y los recursos
  `roles`, `positions`, `users`, `delegations`, `goals`, `attention-types`,
  `attention-subtypes`, `neighbors`, `cases`, `community-organizations`,
  `territories`, `sgr-periods`, `sgr-areas`, `sgr-indicators`, `sgr-targets`,
  `sgr-records`, `sgr-conducts`, `sgr-absences`, `tasks`, `evidence`, `validations`,
  `social-cases`, `comments`, `alerts`.
- Las exportaciones `.xlsx` respetan el filtro y agregan una fila de título con
  la **fecha de generación** (RF-033).
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
- El **acotamiento territorial** vive en un solo lugar:
  `campo_delegacion_de(modelo)` (`apps/common/delegaciones.py`) da la ruta del
  campo por modelo, y `acotar` filtra por la delegación activa. `AcotadoMixin`
  (`vistas_base.py`) lo aplica al listado —y por ende a la exportación—, a la
  consulta, a la edición, al borrado y a las acciones; `BaseViewSet`
  (`apps/api/views.py`) hace lo mismo en la API. Un rol de alcance global no se
  acota. Ver §23.
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

---

## 20. Módulos de la matriz SGR, organizaciones y tubo (implementado)

Fuente: `apps/sgr/`, `apps/comunidad/`, `apps/tubo/`, `apps/common/permisos.py`.

### 20.1 Matriz SGR (`apps/sgr`)

- Modelos: `Periodo` (trimestre, con `situacion` abierto/cerrado/reabierto y
  topes/umbrales configurables), `Area` (puesto: cargo, responsable,
  delegación), `Indicador` (con `cargo`, `tipo_calculo` y `requiere_evidencia`),
  `MetaIndicador` (ponderador y meta por área/indicador/período, con
  sobrescritura por `funcionario`), `RegistroGestion` (la gestión diaria),
  `AjusteConducta` (reclamo o felicitación), `Ausencia` (licencia, vacaciones,
  emergencia, compensatorio), `Evidencia` y `Validacion`.
- Cálculo puro en `apps/sgr/calculos.py`: `porcentaje` (recortado en el
  `tope_item` del período, por defecto 1.2), `ponderado`, `relativo` (logrado ÷
  meta al día, sin tope: 1 = al día), `semaforo` y `total_ponderado`
  (`tope_total`, por defecto 1.5). El semáforo compara el avance contra la
  **meta al día**: VERDE si `avance ≥ objetivo`, NARANJA si
  `avance ≥ umbral_ambar·objetivo` (0.6), ROJO si no.
- Reglas del 4° trimestre en `apps/sgr/validaciones.py` y en
  `RegistroGestion.save/clean`: solo puntúa la etapa **ejecutada**, no la
  preparatoria; el solicitante **delegado** es otra gestión; sin **nombre ni
  teléfono** no puntúa; máximo **7 registros por día** por funcionario; sólo la
  **semana en curso**; y un **período cerrado** bloquea el ingreso.
- **Evidencia y verificación**: `Evidencia` adjunta archivo o vínculo a un
  registro; `Validacion` la aprueba/rechaza/corrige y actualiza el estado del
  registro. Quien registra no valida lo suyo (RNF-004). Un ítem con
  `requiere_evidencia` solo suma cuando el registro está **aprobado** (RN-010).
  La evidencia se adjunta en el **mismo formulario de alta de la actividad**
  (`RegistroGestionForm`: `evidencia_archivo`, `evidencia_vinculo`,
  `evidencia_tipo`) y se crea en la misma petición: la vista web
  (`RegistrosAlta.form_valid`) y el `POST /api/v1/sgr-records/`
  (`RegistroGestionSerializer.create`) crean la `Evidencia` con `autor` = usuario
  autenticado y `tamano` sellado. `Evidencia` vale con **archivo o vínculo**
  (`Evidencia.clean`). Si el indicador exige evidencia, el alta la reclama: la
  regla y el mensaje viven en `validaciones.falta_evidencia`, que comparten el
  formulario y el `RegistroGestionSerializer`. Ver §23.
- **Ausencias**: `Ausencia` (por área, con `desde`/`hasta`) descuenta días de la
  meta al día (`apps/sgr/servicios.py`), que se topa en 100 % (RN-008).
- **Conductas**: `AjusteConducta` (reclamo o felicitación) guarda `medio` y
  exige **respaldo** en las felicitaciones (doc 1). El `valor` por defecto es
  0.1 y el del reclamo depende del cargo (−0.3 en Apoyo Administrativo, −0.2 en
  el resto); más de **2 reclamos** en el período marca alerta a RR.HH.
- **Comentarios y alertas**: `Comentario` cuelga de un registro (RF-035); `Alerta`
  (tipo, severidad, mensaje, resuelta) se genera con
  `manage.py generar_alertas` a partir de tareas vencidas, ítems bajo umbral,
  **ingresos sospechosos** (teléfono muy repetido o cantidad inusual) y
  **organizaciones sin visita** (RF-037/044/060).
- **Concurrencia optimista**: `RegistroGestion.version` sube en cada guardado; el
  formulario de edición envía la versión y avisa si otro usuario ya la cambió
  (RF-034/RNF-002).
- Mantenedores web en
  `/sgr/{periodos,areas,indicadores,metas,registros,conductas,ausencias,evidencias,validaciones,comentarios,alertas}/`.
- **Tableros**: `Tablero` (`/sgr/`) por área con una **barra de avance** (relleno
  = logrado, marca vertical = meta al día), el **cumplido** en % (logrado ÷ meta
  al día, donde 100 % es "al día"), el semáforo, la alerta de reclamos y el
  total/promedio de la delegación (RF-029/049); los valores crudos de logrado y
  meta al día van en el `title` de cada celda y el total se normaliza por el
  número de áreas. `FichaPersonal` (`/sgr/personal/<pk>/`) por persona, con
  marcas de **bajo umbral** y **en tope** (RF-028/045); y `TableroGlobal`
  (`/sgr/global/`) consolidado por cargo (RF-031).

### 20.2 Organizaciones comunitarias (`apps/comunidad`)

- Modelo `Organizacion` (OROC): nombre, domicilio legal, territorio
  (delegación), `tipo`/`subtipo` (territorial o funcional), `situacion`
  (vigente/inactiva/cerrada), `verificacion` (sin-verificar/verificada), socios
  activos y datos del registro de personalidad jurídica.
- **Directiva**: la ficha guarda `presidente`, `tesorero` y `secretario`
  (nombre de cada uno). Ver §25.
- **Vínculo de actividades** (RF-059): `RegistroGestion.actividad`
  (visita/reunión/taller/conformación/otra) y su `organizacion` enlazan la
  actividad con la organización; `Organizacion.ultima_visita` la resume.
- **Sin visita** (RF-060): `Organizacion.sin_visita` marca las que llevan más de
  `MESES_SIN_VISITA` (6) sin una visita, y el generador de alertas las avisa.
- Mantenedor web en `/organizaciones/` y comando
  `manage.py importar_jjvv [--archivo …] [--informe …]`: carga la base de JJVV
  **sin descartar filas** (las dudosas quedan `sin-verificar`) y escribe
  `informe_calidad_jjvv.md` (territorios vacíos o fuera de lista, duplicados,
  socios no numéricos). El territorio **Alfalfares** se agregó a
  `datos_nuevos/delegaciones.json`.

### 20.3 Tubo de trabajo (`apps/tubo`)

- Modelo `TareaTubo`: título, descripción, estado
  (`ingresada → pendiente → en_proceso → realizada`), delegación, territorio
  (sector), tipo (externo/interno), solicitante, responsable, apoyo, avance y
  fechas. Exige responsable y fecha de compromiso (RF-017).
- `HistorialEstado` registra cada cambio de estado (RF-018); `TareaTubo.save`
  lo crea al detectar el cambio. Las transiciones entre estados están
  controladas (`puede_pasar_a`), y `vencida`/`dias_atraso` marcan las tareas
  atrasadas (RF-019).
- El tablero `/tubo/` es un **kanban** de la delegación activa: arriba, una fila
  de cuatro **KPI** (total en tubo, realizadas con tasa de resolución, en
  proceso y pendientes) y abajo una columna por estado, numerada y con código de
  color (gris, rojo, ámbar, verde) que se repite en el borde y el título de la
  tarjeta. Cada tarjeta muestra el código, el documento vinculado, el título, el
  solicitante, el apoyo y el responsable, más un botón con el paso siguiente del
  flujo (`accion_destino`) y la **reasignación** de responsable (RF-053);
  `Mover` (POST) cambia el estado al arrastrar la tarjeta o al pulsar el botón
  (`static/js/tubo.js`). El **historial** se ve en
  `/tubo/tareas/<pk>/historial/`. Visible para el rol `delegado` (y admin,
  coordinador y funcionario). Las tareas **atrasadas** se destacan: la cabecera
  de cada columna muestra cuántas van vencidas y la tarjeta atrasada lleva fondo
  rojo y un distintivo «Atrasada · N días».
- **Tubo de cartas** (RF-054): modelo `Carta` (asunto, correlativo, destinatario
  alcaldesa/delegado, remitente, contacto, estado en proceso/aprobada/finalizada/
  no aplica). Doble vista: **tabla** en `/tubo/cartas/` (listado con el CRUD) y
  **kanban** en `/tubo/cartas/kanban/` (una columna por estado, con arrastre o
  botón «Aprobar/Finalizar»); se alternan con el botón «Ver en kanban» / «Ver en
  tabla». Enlazado en el menú «Cartas». Ver §25.
- **Automatización atención → tubo**: al registrar una `Atencion` nace un
  compromiso en el tubo de su delegación, ligado a la atención
  (`apps/tubo/signals.py`, análogo a la llamada preventiva de `apps/casos`). Ver
  §25.

### 20.4 Permisos de los módulos nuevos

- Claves nuevas de la matriz (§18.2): `community`, `territories`, `sgr`
  (configuración), `sgr_records` (actividades), `sgr_adjustments` (conductas y
  días), `tasks`, `comments`, `alerts`, `evidence`, `validation` y
  `social_cases`.

### 20.5 Descriptor de cargos y catálogo de atención

- `Cargo.funciones` guarda el detalle del *Descriptor de funciones para los
  cargos de las Delegaciones* (la descripción corta sigue en `descripcion`).
- `SubAtencion.forma` (dinero/material/documento/aporte) se suma al catálogo, con
  las sub atenciones del gestor social (Informes sociales, Gestión de subsidios).

### 20.6 Casos sociales (`apps/casos`)

- `CasoSocial` (RF-015/051/052): agrupa hasta **tres atenciones** del mismo vecino
  (`MAX_GESTIONES`, validado en `Atencion.clean`); vecino, responsable, apertura,
  motivo, estado (abierto/seguimiento/cerrado) y reingreso con `caso_anterior`.
- `Atencion.caso` enlaza cada atención con su caso.
- Mantenedor web en `/casos/` y API `social-cases` (módulo `social_cases`).

### 20.7 Flujo principal

- **Atención → Compromiso → Actividad con evidencia → Validación → Meta**: la
  atención registra lo que pide el vecino; el compromiso es la promesa (con
  responsable y fecha); la actividad es lo ejecutado, enlazada al compromiso y a
  su ítem, justificada con un archivo de evidencia.
- Al aprobar la evidencia, el verificador hace que la actividad sume una sola vez
  al puntaje y el compromiso quede **realizado**.

---

## 21. Cierre de brechas (2026-11-15)

Piezas que cerraron los faltantes y parciales de la especificación SGR.

- **RF-050 · Llamadas preventivas.** `apps/casos`: modelo `Llamada` (`LLA`); una
  señal (`apps/casos/signals.py`, conectada en `CasosApp.ready`) crea la llamada
  pendiente al registrar una `Atencion`; mantenedor en `/casos/llamadas/` con
  acción de cierre (`llamadas_cerrar`). Módulo de permiso `cases`.
- **RF-054 · Tubo de cartas.** `apps/tubo`: modelo `Carta` (`CAR`) con estatus
  (en proceso/aprobada/finalizada/no aplica) y totales por estatus en el
  subtítulo; mantenedor en `/tubo/cartas/`. Módulo `tasks`.
- **RF-055 · Agenda del delegado.** `apps/tubo`: vista `Agenda` en
  `/tubo/agenda/`, con los compromisos ordenados por fecha de compromiso y
  exportación `.xlsx`.
- **RN-001 · Suma de ponderadores.** `Area.excepcion_ponderadores` permite la
  excepción; `servicios.resumen_area` expone `suma_ponderadores` y
  `suma_incompleta`, y el tablero/ficha advierten sin bloquear.
- **RF-030 · Actividad reciente.** `servicios.resumen_area` agrega
  `ultimo_ingreso`, `dias_sin_ingreso`, `ingresos` y `promedio_diario`; se
  muestran en la ficha personal.
- **RN-017/018/019 · Caso social.** Parametrizados en `apps/sgr/validaciones.py`
  (`PLAZO_*`, `VALOR_INFORME`, `META_TUBO`) con la línea base inferida.
- **RNF-009 · Evidencias.** `Evidencia.clean` acota formato (jpg/png/pdf) y
  tamaño (5 MB). La misma regla se aplica en el alta de la actividad, web y API:
  el formulario valida el archivo adjunto y `EvidenciaSerializer.validate` invoca
  `Evidencia.clean` (antes la API no la ejecutaba).
- **RNF-005/R9 · Producción.** `config/settings.py` activa HTTPS/HSTS y cookies
  seguras solo con `PRODUCCION_SEGURA=1` (opt-in), porque exige que Apache envíe
  `X-Forwarded-Proto=https`; middleware `apps/common/ratelimit.py` limita los
  intentos de login por IP.
- **RNF-015 · Errores.** Páginas `templates/403.html`, `404.html` y `500.html`.

---

## 22. Datos de volumen, guía, perfil y UI (2026-11-19)

Conjunto de mejoras para que el sistema se vea y se use con datos reales.

- **Volumen demo en `cargar_datos`.** Además de los maestros, el comando siembra
  territorios, vecinos, organizaciones, atenciones (~300), casos, llamadas,
  compromisos (~60), cartas y la matriz SGR (período, áreas, indicadores, metas,
  ~320 actividades, evidencias, validaciones, conductas y ausencias), y genera
  las alertas con `generar_alertas`. Se ejecuta **una sola vez** por base
  (guardia por existencia de atenciones/gestiones) y usa semilla fija. Ver §12.
- **Sidebar plegable.** Los grupos "Trabajo" y "Mantenedores" son `<details>`;
  `js/sidebar.js` recuerda el estado y mantiene abierto el grupo activo. El
  ítem activo se resalta con `seccion` en cada vista. Ver §13.
- **Acciones de fila legibles.** Los chips de acción de los 27 listados muestran
  icono **y** texto; el botón de alta de la cabecera también. Ver §13.
- **Guía de bienvenida.** Tour por pasos con resaltado
  (`js/guia.js` + `static/css/institucional.css`), saltable, que se abre la
  primera vez (`Usuario.guia_vista`) y se puede reabrir con `?guia=1`. El aviso
  de "vista" va por `cuentas:guia_vista` (POST). Ver §10.2 y §13.
- **Mi perfil.** Página `/perfil/` (`MiPerfil`) con los datos del usuario, sus
  contadores y el **cambio de contraseña** (exige la actual). Enlace en el menú
  de usuario. Ver §10.2.
- **Panel con visualización sin librerías.** `inicio.html` suma un bloque de
  estado del período SGR (semáforo por área) y "últimas atenciones", calculados
  en `apps/panel/servicios.resumen_visual`. No se agregó ninguna librería de
  gráficos.

---

## 23. Revisión de seguridad y coherencia (2026-11-23)

Cierre de los hallazgos de la revisión de los tres cambios paralelos (evidencia
en el alta web, evidencia en la API y rediseño del tablero SGR).

- **Acotamiento territorial completo (IDOR).** Antes solo el listado se acotaba
  por delegación; el detalle, la edición, el borrado, las acciones y toda la API
  operaban por `pk` sin filtrar delegación, así que un perfil acotado podía
  leer/editar/borrar registros de otra delegación conociendo la clave. Ahora la
  ruta del campo se resuelve por modelo en `apps/common/delegaciones.py`
  (`CAMPO_DELEGACION` + `campo_delegacion_de`) y la aplican `AcotadoMixin` (web,
  `apps/common/vistas_base.py`) y `BaseViewSet` (API, `apps/api/views.py`) en
  todas las operaciones. Una `Llamada` se acota por `vecino__territorio` (puede
  no tener atención asociada).
- **RN-010 en una sola fuente.** La exigencia de evidencia y su mensaje viven en
  `apps/sgr/validaciones.py::falta_evidencia`; la consumen el formulario web y el
  serializer, y la validación del archivo (formato y tamaño) sigue en
  `Evidencia.clean`. `Evidencia` ahora vale con **archivo o vínculo**, coherente
  con el alta que admite cualquiera de los dos.
- **`model.clean()` en la API.** `LimpiaModeloMixin` ejecuta el `clean()` del
  modelo en los serializers, como hace un `ModelForm`: la API ya no salta las
  reglas de cruce de campos (reingreso de `CasoSocial`, `responsable`+`fecha` de
  `TareaTubo`, `término ≥ inicio` de `Periodo`, `meta > 0` de `MetaIndicador`,
  respaldo de la felicitación y segregación de funciones de `Validacion`).
- **Validadores repuestos.** Campos redeclarados que perdían el validador del
  modelo lo recuperan (`contact_phone`, `backing`, `pj_registry`,
  `directive_registry`); `evidence_link`/`link` vuelven a `URLField`;
  `quantity`/`active_members` acotan a ≥1/≥0; `NuevaPasswordSerializer` valida la
  contraseña.
- **Verificación.** `bash scripts/verificar.sh` en verde: check, migraciones,
  carga de datos, ruff, pytest y smoke de rutas + API.

---

## 24. Ajustes de UI: buzón, kanban y paginador (2026-11-23)

- **Se retira el buzón de trabajo**: se eliminan la ruta `/buzon/`
  (`panel:BuzonTrabajo`), la función `panel.servicios.buzon`, la plantilla
  `templates/buzon.html`, sus estilos y su enlace en el menú. El trabajo
  accionable se sigue viendo en cada módulo; el panel de inicio conserva sus
  tarjetas por rol.
- **Kanban de compromisos**: las tareas atrasadas (`TareaTubo.vencida`) se
  destacan con fondo rojo, un distintivo «Atrasada · N días» y el conteo de
  atrasadas en la cabecera de cada columna (`apps/tubo/views.py` y las clases
  `.kanban-tarjeta-atrasada` / `.kanban-atrasadas`). Ver §20.3.
- **Selector de filas por página** en todos los listados: `ListadoBase` ofrece
  8, 16, 32 o 64 filas (`?por=`), con 8 por defecto; el selector vive en
  `templates/listado.html` y `static/js/busqueda.js` lo conserva al buscar. Ver
  §6.3 de `vision.md`.
- Verificación: `bash scripts/verificar.sh` en verde.

---

## 25. Cartas, automatización y directiva (2026-11-23)

- **Tubo de cartas visible** (RF-054). El módulo ya existía (modelo, vistas,
  rutas, plantilla) pero había quedado sin enlace en el menú. Se repone bajo el
  grupo «Trabajo» como «Cartas» (`tubo:cartas`) y se le da paridad con el resto
  del CRUD: edición, baja lógica (`cartas_desactivar`) y reactivación
  (`cartas_reactivar`). Sección `tubo_cartas` para el resaltado del menú.
- **Tabla y kanban, alternables.** Compromisos y cartas tienen las dos vistas y
  un botón para pasar de una a otra: compromisos en `/tubo/` (kanban) y
  `/tubo/tareas/` (tabla); cartas en `/tubo/cartas/` (tabla) y
  `/tubo/cartas/kanban/` (kanban). El kanban trae una columna por estado,
  tarjetas arrastrables y botón «Aprobar/Finalizar» (cartas) o el paso siguiente
  (compromisos); reutiliza `static/js/tubo.js` y `CartaMover`/`Mover`
  (`tubo:cartas_mover` / `tubo:tareas_mover`), que validan el estado destino. El
  CRUD completo vive en la tabla.
- **Automatización atención → tubo.** `apps/tubo/signals.py` registra un
  `post_save` sobre `Atencion`: cada atención nueva crea un `TareaTubo`
  (compromiso, estado `ingresada`) en el tubo de su delegación, ligado a la
  atención y con el funcionario como responsable. Es idempotente (`get_or_create`
  por atención), igual que la llamada preventiva de `apps/casos`. Se engancha en
  `TuboConfig.ready`.
- **Directiva de la organización.** `Organizacion` suma `presidente`, `tesorero`
  y `secretario` (nombre de cada uno); se ven en el alta, la ficha de consulta,
  la exportación y el contrato de la API (`president`/`treasurer`/`secretary`).
  Migración `comunidad/0003_organizacion_directiva`.
- Verificación: `bash scripts/verificar.sh` en verde.
