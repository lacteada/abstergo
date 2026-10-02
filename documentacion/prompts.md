# Evidencia de uso de IA — construcción de `/abstergo`

Registro curado de las sesiones que **construyeron** el sistema (Evaluación Sumativa #2).
Se conservan solo los prompts que produjeron algo del proyecto, agrupados por área de
desarrollo, cada uno con lo que se aplicó.

**Qué se dejó fuera.** Los insumos de análisis, el mockup estático y el desarrollo de la
Evaluación 1 no construyen `/abstergo`; van resumidos al final, en el
[índice de sesiones](#índice-de-sesiones-y-disposición).

**Volcado completo.** El registro original (todas las sesiones, con las respuestas
completas) sigue en el historial de git, recuperable con:

```bash
git show 3277bb1:documentacion/prompts.md
```

**Cómo leer cada bloque.** El prompt va citado tal como se escribió; debajo, en negrita,
lo que se aplicó al proyecto.

---

## 1. Arranque y planificación del build

**Sesión `d636a27a` · 2026-09-21.** Primer esbozo del alcance de la aplicación nueva.

> Django: MD summary to-do: - Login + Password Recovery (Email Verification Code) - Crud: Roles, Users, Delegaciones Municipales, Metas, Tipo de atencion, Sub Atencion, Vecinos. all working on cloud AWS using MySQL

**Qué se aplicó.** Se creó `~/code/ina/proyect/notes/todo-django-desde-cero.md`: checklist
en 4 bloques (alcance, autenticación, los 7 CRUD y AWS + MySQL), con las entidades y sus
relaciones.

> Its from scratch this time

**Qué se aplicó.** Se fijó que el proyecto se construye desde cero, en carpeta nueva, sin
reutilizar código del proyecto anterior.

> si es posible guiar en cada seccion, que tecnologias usar, quiero bootstrap

**Qué se aplicó.** Se agregó una guía de tecnologías por sección al mismo documento:
usuario propio de Django, vistas basadas en clases, borrado lógico, `django-filter` y
`EC2 + gunicorn` para el despliegue.
*(Desvío asumido: el front terminó sin Bootstrap; usa el framework institucional +
`institucional.css`. Ver `07_Frontend.md`.)*

---

## 2. Base de datos: reestructura

**Sesión `9193e990`.** El esquema tenía redundancias; se simplificó antes de seguir.

> ayúdame a reestructurar la base de datos primero, hay demasiado

**Qué se aplicó.** Diagnóstico: `Delegacion.activo` duplicaba el borrado lógico;
`PerfilUsuario.estado` duplicaba `is_active`; `Meta` no se relacionaba con nada; y el
borrado lógico existía en 3 tablas, así que "Eliminar" significaba dos cosas distintas.
Se escribió y aprobó el plan `abstergo-reestructura-bd.md` y se implementó:

- `apps/common/soft_delete.py` partido en `Eliminado` (campo + `eliminar()`) y
  `BorradoLogico` (además cambia los gestores `objects` / `todos`).
- `Usuario` propio (`AbstractUser` + `Eliminado`), sin `username`, con `email` único y
  nulable como `USERNAME_FIELD`, y `rol` y `delegacion` en el propio usuario.
  `AUTH_USER_MODEL = "cuentas.Usuario"`; se eliminaron `PerfilUsuario` y la señal
  `post_save`.
- `Meta` con FK a `Delegacion`; `Delegacion` sin `activo`; borrado lógico en las 7 tablas.
- Migraciones rehechas (Django exige `AUTH_USER_MODEL` antes de la primera migración).
  Sin pérdida: los 46 registros se regeneran desde `datos_nuevos/`.
- `cargar_datos` actualizado: los usuarios se buscan por nombre y apellido, porque un
  correo nulo no sirve como llave de `update_or_create`.

**Verificado** sobre un SQLite temporal (sin tocar MariaDB): primera corrida `46 creados`,
segunda `0 creados, 46 actualizados`; `username` no aparece en la migración; dos usuarios
sin correo conviven con contraseña inutilizable; y el flujo `recuperar → validar → nueva
contraseña → login` funciona de punta a punta.

---

## 3. Autenticación, OTP y correo

**Sesión `9193e990`.** El flujo de recuperación ya estaba implementado; faltaba el envío
real de correo.

> cómo configuro la confirmación por código por correo en /abstergo en mi EC2

**Qué se aplicó.** El OTP ya vivía en `apps/cuentas/views.py::_guardar_otp` (6 dígitos con
`secrets`, guardado en la sesión con vencimiento y sin reutilización). Se verificó contra
el código de Django 6.1.1 que el ajuste `MAILERS` y las `OPTIONS` del backend SMTP son
correctos, así que bastaba con cambiar el `.env` de `console.EmailBackend` a SMTP.

> no tengo número para verificación

**Qué se aplicó.** Se descartaron las vías que exigen teléfono (Gmail, SES). Se eligió
**Brevo** por correo: `smtp-relay.brevo.com`, puerto **587** (no 465, porque el bloque
`MAILERS` solo pasa `use_tls`), con la SMTP key como contraseña.

> antes de importar usuarios, necesito que no tengan correo, sólo el mantenedor tendrá mi correo

**Qué se aplicó.** Se ajustaron los correos antes de importar, de modo que el cargador no
cambió. Quedó documentado que `Recuperar` busca por `email__iexact`, así que los usuarios
sin correo no entran al flujo de recuperación por diseño.

---

## 4. Front-end

**Sesión `9193e990`.** Correcciones de interfaz sobre los listados.

> arregla /abstergo, sus tablas en front end al hacer zoom se desarman en bloques en vez de mantener una tabla

**Qué se aplicó.** El `frameworkV1.css` traía un media query
`@media (min-width: 350px) and (max-width: 768px)` que convertía **cualquier** `table` en
tarjetas (`tr`/`td` con `display: block`, `thead` oculto); el zoom bajaba el viewport de
768 px y se disparaba. Fix: se acotaron esas reglas a `.table-responsive table ...`, y
`.tabla-envoltura` pasó a hacer scroll horizontal en vez de partir la tabla.

> usuario es ICONO > Nombre y abajo su rol con un dropdown para salir de la sesion - el boton nuevo debe seguir "+ Nuev@ [Entidad]" (+ Nuevo usuario), a la derecha del hint se debe mostrar un icono de luca que represente la funcion del input, lupa negra simple

**Qué se aplicó.** En `base.html`, el usuario es un `<details class="usuario">` con icono,
nombre y rol, y menú «Cerrar sesión» (logout por POST + CSRF). El botón es
`+ {{ etiqueta_nueva }}`, con la etiqueta declarada una vez en la vista
(`vistas_base.py`, atributo `etiqueta_nueva`). El buscador lleva una lupa SVG negra a la
derecha; se ocultó la cruz nativa del `type="search"`.

> quita el underline del boton nuevo y haz el boton mas grande sin modificar el texto, el texto quizas en bold

**Qué se aplicó.** En `frameworkV1.css`, `.btn-muni`: `text-decoration: none`,
`padding: 10px 18px`, `font-weight: bold`, `border: 0`, `border-radius: 6px`. El texto no
cambió; afecta a todos los botones `.btn-muni` (Nuevo, Guardar, Eliminar, Ingresar).

---

## 5. Entorno local (diagnóstico)

**Sesión `9193e990`.** El `runserver` no arrancaba y no se sabía con qué configuración
había estado corriendo el sistema.

> reinicia pagina

**Qué se aplicó.** Se mató el `runserver 8000 --noreload` y, al relanzar, apareció el
bloqueo: el venv no tiene `mysqlclient` y no hay MariaDB local, así que `runserver` aborta
con `Error loading MySQLdb module`.

> esta corriendo con mysqlite por ahora que yo sepa, en produccion se le open maira

**Qué se aplicó.** Se verificó que `abstergo` (minúscula) está configurado a MariaDB
(`ENGINE=django.db.backends.mysql`), que no hay configuración SQLite ni `db.sqlite3`, y que
los proyectos con SQLite son las otras carpetas.

> y como estaba corriendo?

> abstergo en minusculas, no salgas de ahi

> entonces no sabes como funcionba?

**Qué se aplicó.** En los registros de la sesión anterior se encontró que el server corría
con `using settings 'settings_sqlite'`: la sesión `d1b761b0` había creado en su scratchpad
un `settings_sqlite.py` (`from config.settings import *`, sobreescribe solo `DATABASES`) y
un `abstergo.sqlite3`. El comando real era:

```bash
PYTHONPATH=<scratchpad de la sesión> \
DJANGO_SETTINGS_MODULE=settings_sqlite \
./venv/bin/python manage.py runserver 8000 --noreload
```

Nunca hubo MariaDB local: se usó un SQLite temporal, fuera del repo, por eso la
configuración no aparecía en el proyecto.

---

## 6. Documentación

**Sesión `9193e990`.** Cierre de la evidencia y las guías de estudio.

> quiero que documentes todo el chat, sigue desde la documentacion anterior, tambien necesito que documentes en md el fornt y en otro el back end para estudio

**Qué se aplicó.** Se crearon `07_Frontend.md` (guía del front) y `08_Backend.md` (guía del
back), y este `prompts.md` como evidencia de IA. Más adelante se sumaron
`10_Guia_Backend.md`, `11_Backend_Explicado.md` y `12_Recorrido_Completo.md`.

---

## Índice de sesiones y disposición

| Sesión | Fecha | Tema | Disposición |
|---|---|---|---|
| `d636a27a` | 2026-09-21 | Plan del login, la recuperación y el CRUD | **Conservada** (§1) |
| `9193e990` | 2026-09-26 | Front-end, autenticación/OTP, base de datos y entorno | **Conservada** (§2-6) |
| `be943f63` | 2026-09-05 | Interpretación de requerimientos y diagramas UML | Descartada |
| `3e0904b3` | 2026-09-14 | Planificación del mockup estático | Descartada |
| `e2ab7524` | 2026-09-25 | Análisis de laserena.cl e insumos 00-05 | Descartada |
| `1cfc96a2` | 2026-09-07 | Mockup del código de 6 dígitos | Sin prompts en el volcado |
| `b8bba5d8` | 2026-09-03 | Revisión/layout de la Evaluación 1 | Descartada |
| `da55d7d2` | 2026-09-04 | Estudio de urls y plantillas de la Evaluación 1 | Descartada |
| `d09ec115` | 2026-09-03 | Blueprint de arquitectura del backend | Sin prompts en el volcado |
| `d1b761b0` | 2026-09-26 | Planificación y construcción de la Evaluación 2 | Sin prompts en el volcado |

### Por qué se descartaron

- **`be943f63` (Interpret Requirements):** interpretación de la guía de requerimientos para
  diagramar UML/flowchart. No produjo código de `/abstergo`.
- **`3e0904b3` (Mockup Planning):** mockup HTML estático publicado en `gh-pages`,
  precursor que el rediseño final reemplazó.
- **`e2ab7524` (Frontend Design Documentation):** análisis del portal de referencia y
  redacción de los insumos `00` a `05`, que no son entregables del proyecto.
- **`b8bba5d8` y `da55d7d2`:** desarrollo y estudio de la **Evaluación 1** (apps
  `actividades`, `agenda`, `delegacion`, dark mode, refactor). Es el proyecto de origen de
  los datos, no el sistema `/abstergo`.
- **`1cfc96a2`, `d09ec115`, `d1b761b0`:** sesiones sin prompts capturados en el volcado
  (solo encabezado).

---

*El volcado completo de todas las sesiones sigue disponible en git:
`git show 3277bb1:documentacion/prompts.md`.*
