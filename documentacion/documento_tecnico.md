# Documento técnico — Sistema Municipal de Gestión de Atención Ciudadana

El código está en `https://github.com/lacteada/abstergo`.

## 1. Descripción del proyecto

Los datos viven en una base de datos relacional y el sistema se administra desde Django Admin, con un front-end de listados construido sobre plantillas Django.

Temática: gestión de atención ciudadana de las delegaciones municipales de La Serena.

Funcionalidades implementadas hasta ahora:

- Modelo de datos propio de 7 entidades, con migraciones aplicadas.
- Carga de los datos desde JSON a la base, por comando de gestión y con el ORM.
- Django Admin con las 7 entidades registradas, navegables y buscables.

También están implementados el front-end con los 7 listados y su CRUD completo, y la autenticación con código OTP.

## 2. Arquitectura

```
abstergo/
├── manage.py
├── .env, .env.example, requirements.txt
├── config/                  settings, urls, wsgi
├── apps/
│   ├── common/              compartido, no es una app de Django
│   │   ├── vistas_base.py   las 4 vistas genéricas de los mantenedores
│   │   ├── admin_base.py    el Admin en solo lectura
│   │   └── soft_delete.py   el borrado lógico
│   ├── cuentas/             Rol, PerfilUsuario, autenticación
│   ├── organizacion/        Delegacion
│   ├── catalogos/           Meta, TipoAtencion, SubAtencion
│   ├── ciudadanos/          Vecino
│   └── panel/               Inicio y comando de carga
├── datos_nuevos/            el JSON de importación, un archivo por entidad
├── templates/               armazón, listados y las pantallas de acceso
├── static/                  css, js, img
└── documentacion/           planificación, traslado, prompts y documento técnico
```

Decisiones de estructura:

- Las 5 apps viven bajo `apps/`, y cada una se registra por su ruta completa (`apps.cuentas`), no por el nombre suelto.
- `apps/common/` no es una app de Django: no está en `INSTALLED_APPS` y no tiene modelos. Es solo el paquete donde viven las tres piezas compartidas, para que se lean como lo que son y no como una app más.
- `config/` guarda la configuración del proyecto, separada de los módulos.
- La app `panel` no tiene modelos: aloja el comando de carga y, más adelante, la vista de Inicio.

## 3. Base de datos y ORM

Motor: MariaDB. Driver: `mysqlclient`. Las credenciales salen del `.env`, nunca del código.

### Entidades y relaciones

| Tabla | Campos | Relación |
|---|---|---|
| `organizacion_delegacion` | codigo, nombre, direccion, comuna, activo, eliminado | — |
| `cuentas_rol` | nombre, descripcion, eliminado | — |
| `cuentas_perfilusuario` | usuario, rol, delegacion, estado | → Rol, → Delegacion |
| `catalogos_meta` | nombre, descripcion | — |
| `catalogos_tipoatencion` | nombre, descripcion, eliminado | — |
| `catalogos_subatencion` | nombre, tipo_atencion | → TipoAtencion |
| `ciudadanos_vecino` | nombre, rut, direccion, telefono, territorio, tipo_gestion, estado | → Delegacion |

Cuatro relaciones en total:

- `PerfilUsuario` → `Rol`
- `PerfilUsuario` → `Delegacion`
- `SubAtencion` → `TipoAtencion`
- `Vecino` → `Delegacion`

`Meta` queda sin relaciones, por decisión consciente: los cargos del origen no se modelaron, así que no hay de dónde colgarla. Se detalla en `traslado_de_datos.md`.

### Integridad

Ninguna llave foránea borra en cascada: las cuatro relaciones entre entidades usan `PROTECT`, y `PerfilUsuario` → `User` es la única en cascada, porque el perfil es una extensión del usuario y no tiene sentido sin él.

`PROTECT` por sí solo dejaba el mantenedor inservible: no se podía dar de baja una Delegación o un Rol que estuviera en uso. La solución no fue cambiar el borrado a cascada ni a `SET_NULL`, porque `SET_NULL` habría dejado al vecino sin el dato de su territorio.

La solución fue el **borrado lógico** en las tres entidades que otras referencian:

| Entidad | Por qué |
|---|---|
| `Delegacion` | la referencian `Vecino` y `PerfilUsuario` |
| `Rol` | lo referencia `PerfilUsuario` |
| `TipoAtencion` | lo referencia `SubAtencion` |

Las tres heredan de un modelo abstracto `BorradoLogico` que aporta:

- Una columna `eliminado`, fecha nula mientras la fila está vigente.
- Un gestor `objects` que esconde las dadas de baja, y un gestor `todos` que las ve todas.
- Un método `eliminar()` que escribe la fecha en vez de borrar.

El botón de eliminar del mantenedor llama a `eliminar()` en esas tres. La fila sale del listado y nadie pierde la referencia: el vecino sigue mostrando su territorio y el perfil su rol. `PROTECT` queda como red de seguridad ante un `DELETE` directo desde phpMyAdmin.

En los otros cuatro mantenedores el borrado es real, y la fila desaparece de la base.

Efectos asumidos, todos conscientes:

- Una Delegación dada de baja sigue ocupando su `codigo`, y un Rol su `nombre`. No se puede crear otro con el mismo valor mientras la fila esté marcada.
- Recargar el JSON con `cargar_datos` restaura lo dado de baja: el comando usa el gestor sin filtro y limpia la fecha, para seguir siendo idempotente.
- `Vecino.territorio` es obligatorio, así que un vecino siempre tiene territorio.

Django no delega el borrado a la base: no emite cláusulas `ON DELETE` al crear las tablas. Resuelve las referencias desde Python, así que el comportamiento es el mismo en SQLite y en MariaDB.

El modelo `Usuario` no se duplica: se usa el `auth.User` de Django y un perfil con `OneToOne` que aporta el rol, la delegación y el estado. El perfil se crea solo, con una señal `post_save` sobre `User`.

### Migraciones

Cuatro archivos `0001_initial.py`, uno por app con modelos: `cuentas`, `organizacion`, `catalogos` y `ciudadanos`.

### Consultas ORM

Los datos nunca se leen de JSON en tiempo de ejecución: todo pasa por el ORM. Ejemplo real, tomado de la verificación:

```python
Vecino.objects.filter(territorio__nombre="Centro")
```

Django genera el SQL solo, con su `JOIN`:

```sql
SELECT "ciudadanos_vecino"."id", "ciudadanos_vecino"."nombre", ...
FROM "ciudadanos_vecino"
INNER JOIN "organizacion_delegacion"
  ON ("ciudadanos_vecino"."territorio_id" = "organizacion_delegacion"."id")
WHERE "organizacion_delegacion"."nombre" = Centro
ORDER BY "ciudadanos_vecino"."nombre" ASC
```

No hay SQL escrito a mano en el proyecto, ni uso de `cursor()` o `raw()`.

## 4. Carga de datos

El JSON nuevo vive en `datos_nuevos/`, un archivo por entidad, con los mismos nombres de campo que las columnas. El comando lo recorre y escribe con el ORM:

```bash
python manage.py cargar_datos
```

- Usa `update_or_create`, así que es reejecutable sin duplicar.
- Recorre en orden de dependencia: delegaciones y roles, después usuarios, luego los catálogos y al final vecinos.
- Informa cuántos registros creó y cuántos actualizó.
- Asigna la contraseña de los usuarios migrados con `set_password()`, tomándola del `.env`.

Resultado verificado: 46 registros creados en la primera ejecución, y en la segunda, 0 creados y 46 actualizados.

Conteos finales: 6 delegaciones, 6 roles, 6 perfiles, 6 metas, 4 tipos de atención, 8 sub atenciones y 10 vecinos.

El mapeo campo por campo desde los JSON de origen, con lo descartado y su justificación, está en `traslado_de_datos.md`.

## 5. Django Admin

Las 7 entidades están registradas, con `list_display`, `search_fields` y `list_filter`. Se navega entre entidades relacionadas con `autocomplete_fields` en las llaves foráneas.

El Admin está en **solo lectura**: ve, busca y navega, pero no permite crear, modificar ni eliminar. Las tres restricciones se escriben una sola vez, en una clase base `SoloLecturaAdmin`, de la que heredan las 7 clases. Para revertirlo basta con quitar esos tres métodos.

Es una decisión consciente y asumida: el Admin queda para consulta y navegación, sin alta, modificación ni borrado.

## 6. Front-end

Los 7 mantenedores tienen listado, alta, edición y borrado sobre plantillas Django y datos del ORM. Son 28 vistas, todas genéricas: `ListView`, `CreateView`, `UpdateView` y `DeleteView`.

### Cómo se evita repetir código

- `apps/common/vistas_base.py` define lo común: el título, la sección del sidebar, el buscador sobre los campos que cada módulo declara y el `select_related` de las llaves foráneas que la plantilla recorre.
- Cada `views.py` declara solo sus datos: modelo, formulario, título, plantilla y nombres de ruta.
- `templates/listado.html` tiene el armazón del listado una sola vez: título, buscador, botón Nuevo, tabla y columna de acciones.
- Cada módulo aporta un template de unas 20 líneas con sus columnas, que hereda de `listado.html` y llena los bloques `encabezado` y `fila`.
- `templates/formulario.html` y `templates/confirmar.html` sirven a los 7 módulos para el alta, la edición y la confirmación del borrado.
- El sidebar está en `templates/base.html` y marca la sección activa según el módulo.

### El buscador

Vive en la vista, no en la plantilla: `get_queryset` filtra con `icontains` sobre los campos declarados. Los datos llegan al template ya resueltos. Buscar `rural` en Vecinos devuelve los vecinos cuyo **territorio** se llama así, porque el filtro cruza la llave foránea y el ORM arma el `JOIN`.

### Borrado

El botón de eliminar llama a `eliminar()` en las tres entidades con borrado lógico y a `delete()` en las otras cuatro.

### Diseño

Sin Bootstrap. El framework institucional de laserena.cl aporta la tipografía, los botones, la escala de texto y la paleta; `static/css/institucional.css` aporta lo que ese framework no trae: la grilla, el sidebar del mockup, el header, la tabla y los badges de estado. La tipografía la declara el framework, y en Linux resuelve a la del sistema.

## 7. Autenticación

Cuatro pantallas, siguiendo el mockup §1 a §4:

- **Login** por correo y contraseña contra `auth.User`. En los datos migrados el correo es el `username`, así que se usa el formulario estándar de Django con las etiquetas cambiadas.
- **Recuperar**: pide el correo y genera un código de 6 dígitos.
- **Validar**: los 6 dígitos, con la barra decorativa del mockup.
- **Nueva contraseña**: valida contra `AUTH_PASSWORD_VALIDATORS` y guarda con `set_password()`.

Detalles:

- El código vive en la sesión: no necesita tabla propia, y no se puede reutilizar porque se borra al usarlo.
- Vence a los 10 minutos, valor que sale de `OTP_EXPIRY_MINUTES` en el `.env`.
- Hay un reenvío: `POST /reenviar/` regenera el código desde la sesión, sin volver a pedir el correo.
- La respuesta al pedir el código es la misma exista o no el correo, para no revelar qué cuentas hay.
- El envío sale del `.env`: consola en desarrollo, SMTP en el EC2.
- El Admin conserva su propio login y su propio superusuario, aparte del login del sistema.

## 8. Variables de entorno

Ninguna configuración sensible está escrita en el código. `settings.py` lee el `.env` con `python-dotenv`.

Llaves del `.env`:

- Django: `SECRET_KEY`, `DEBUG`, `ALLOWED_HOSTS`.
- Base de datos: `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT`.
- Localización: `LANGUAGE_CODE`, `TIME_ZONE`.
- Correo: `MAILER_BACKEND`, `EMAIL_HOST`, `EMAIL_PORT`, `EMAIL_HOST_USER`, `EMAIL_HOST_PASSWORD`, `EMAIL_USE_TLS`, `DEFAULT_FROM_EMAIL`.
- Autenticación: `OTP_EXPIRY_MINUTES`, `PASSWORD_MIN_LENGTH`, `USUARIOS_PASSWORD_INICIAL`.

`.env.example` se versiona con las mismas llaves y sin valores; el `.env` está excluido por `.gitignore`.

Nota técnica: Django 6.1 reemplazó `EMAIL_BACKEND` por `MAILERS`. Las `OPTIONS` de cada correo se pasan como argumentos al backend, y cada backend rechaza las que no conoce, así que solo se declaran cuando el backend configurado es el de SMTP. En desarrollo se usa el de consola.

## 9. Uso de herramientas de IA

El registro completo de prompts y respuestas, extraído del historial de sesiones, está en `prompts.md`.

Aplicación concreta:

- La estructura de apps bajo `apps/` y los settings alimentados por `.env`.
- El modelo de datos y las relaciones entre las 7 entidades.
- El comando de carga idempotente con `update_or_create`.
- El borrado lógico en las tres entidades referenciadas, para poder dar de baja una Delegación o un Rol en uso sin perder la referencia.
- Las vistas base compartidas, para que los 7 módulos no repitan el mismo código.
- La detección de que `EMAIL_BACKEND` ya no es la vía en Django 6.1, y de que el loader de plantillas cachea siempre, ambas verificadas contra el código fuente del framework instalado.

## 10. Evidencias pendientes

Esta sección se completa cuando el sistema esté desplegado en el EC2.

- **AWS:** capturas de la instancia, de la terminal y del proyecto en ejecución.
- **GitHub:** capturas del repositorio, del historial de commits y de la clonación en la instancia.
- **phpMyAdmin:** capturas de las 7 tablas, de sus relaciones y de los registros almacenados.
- **Front-end:** capturas de Inicio, de los 7 listados y de un alta.
- **Autenticación:** capturas de las cuatro pantallas.
