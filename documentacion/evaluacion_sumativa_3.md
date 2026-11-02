# Evaluación Sumativa #3 — Alineación con el sistema (Abstergo)

Continuación de la Sumativa #2. A partir de esta entrega, **toda la gestión se hace desde plantillas** (`Django Templates` + formularios + ORM), sin depender de `Django Admin`. Este documento mapea cada requisito de la evaluación a lo implementado y a cómo se demuestra. Ruta del proyecto: `~/code/ina/backend/abstergo`.

## 1. Mapa requisito → implementación → evidencia

**Autenticación y acceso**

- Ingreso con usuario (correo) y contraseña → `apps/cuentas/urls.py` (login), `forms.py` (`FormularioLogin`). Se demuestra entrando con un usuario sembrado.
- Cierre de sesión → `cuentas:logout` (por POST, desde el menú de usuario). Se demuestra cerrando sesión.
- Protección de vistas → `LoginRequiredMixin` en todo el CRUD y el panel. Se demuestra abriendo una URL interna sin sesión (redirige al login).
- Restricción por perfil → `apps/common/vistas_base.py` (`PermisoRequeridoMixin`) + `apps/common/permisos.py` (matriz). Se demuestra con un perfil sin permiso: recibe 403 y no ve el módulo en el menú.

**Perfiles de usuario (mínimo 3)**

- Tres perfiles con permisos diferenciados: ver §2.
- Creación de usuarios → `cuentas:usuarios_nueva` (alta con invitación por correo).
- Asignación de grupos → cada `Rol` se refleja como `auth.Group` (ver §5); al asignar el rol, el usuario queda en su grupo.
- Acceso diferenciado → el menú lateral y el dashboard cambian según el perfil.

**Recuperación de contraseña por correo**

- Solicitud → `cuentas:recuperar` (`apps/cuentas/otp.py:solicitar`). No revela si el correo existe.
- Token seguro → código OTP de 6 dígitos + enlace firmado (`signing.dumps` con sal propia).
- Envío del enlace → correo HTML/texto (`templates/correo/recuperacion.html`).
- Validación → `otp.verificar` (código) o `otp.recuperacion_de_enlace` (enlace); el primero que se use anula al otro.
- Nueva contraseña → `cuentas:nueva_password` y `cuentas:recuperar_enlace`.
- Confirmación → aviso de éxito y reactivación de la cuenta (al pedir recuperación se deshabilita hasta guardar la nueva).

**Django Admin**

- Postura: ver §4. Las operaciones del alcance evaluado van por plantillas.

**Dashboard por perfil**

- Panel diferenciado por perfil → `apps/panel/views.py` (`Inicio`), `apps/panel/servicios.py` (`acciones_del_rol`, `estadisticas`), `templates/inicio.html`. Ver §2 para qué ve cada perfil.

**Mantenedores (mínimo 2, con CRUD completo: crear, buscar, listar, modificar, eliminar)**

- Delegaciones Municipales, Cargos, Roles, Usuarios, Metas, Tipos de atención, Sub atenciones y Vecinos (8 mantenedores).
- Cada uno: `ListadoBase` (listar/buscar/paginar/exportar), `AltaBase`, `EdicionBase`, `ConsultaBase`, `BorradoBase`, `DesactivarBase`/`ReactivarBase`.
- Evidencia: `/delegaciones/` y `/vecinos/`, por ejemplo.

**Transacciones (mínimo 1, con 2+ entidades relacionadas)**

- Registro de atención → `apps/atenciones/views.py: CrearAtencion`. Involucra `Vecino`, `TipoAtencion`, `SubAtencion`, `Delegacion` y `Usuario` (funcionario). Valida en servidor que la sub atención pertenezca al tipo; el JavaScript solo oculta opciones.

**Requisitos técnicos**

- AWS EC2 (despliegue), GitHub (repositorio e historial), MariaDB, Django ORM, migraciones, variables de entorno (`.env`), control de versiones.
- Verificación reproducible: `bash scripts/verificar.sh`.

## 2. Perfiles de usuario

El sistema define los perfiles como **roles** (`Rol.codigo`). Se mapean a los tres perfiles de la evaluación:

| Perfil de la evaluación | Rol(es) del sistema | Acceso |
|---|---|---|
| Administrador | `admin` | Total: mantenedores, transacciones, usuarios, roles y visión global (todas las delegaciones). |
| Supervisor | `coordinador` | Intermedio: alcance global de lectura sobre la operación; sin administración de usuarios/roles. |
| Administrativo | `delegado`, `funcionario`, `verificador`, `consulta` | Mínimo: acotado a su delegación; consulta y registro de la operación según su rol y cargo. |

Además de la categoría de acceso (rol), cada persona puede tener un **cargo** (puesto funcional de la delegación), que suma permisos sobre los módulos operativos (`MATRIZ_CARGO`). Así, dos personas con el perfil Administrativo pueden diferir según su cargo (p. ej. `gestor-social` vs `apoyo-administrativo`).

**Dashboard por perfil**

- Administrador: ve todos los mantenedores y las estadísticas globales de todas las delegaciones.
- Supervisor: ve la operación (atenciones, vecinos, catálogos) con alcance global de lectura; no ve administración de usuarios/roles.
- Administrativo: ve solo lo que su rol y cargo permiten, acotado a su delegación; el contador de atenciones se filtra a su territorio.

## 3. Bootstrap — desvío asumido

El front se construyó con el framework institucional de la organización (`static/css/frameworkV1.css` + `institucional.css`): grilla propia, componentes de tabla, formularios, modales y avisos (SweetAlert2 vendorizado), sin Bootstrap. Se mantiene esta decisión para no romper la identidad visual del municipio.

Cumple los requisitos de fondo de la rúbrica: **Django Templates**, formularios de Django con **validación en el servidor**, CRUD completo y diseño responsivo (la grilla usa los puntos de corte de Bootstrap 5.3 como referencia). El desvío respecto de la librería Bootstrap es de presentación, no de capacidad.

## 4. Django Admin — postura

No se usa para operar el sistema. Todas las operaciones del alcance evaluado —mantenedores y transacción— se ejecutan desde plantillas propias. Los modelos siguen registrados en el Admin como respaldo técnico del superusuario, pero **el flujo de trabajo demostrado no depende de él**. La carga de datos se hace con `python manage.py cargar_datos` (idempotente), no desde el Admin.

## 5. Permisos y grupos

- **Autorización real**: la matriz de `apps/common/permisos.py` (rol × módulo y cargo × módulo), aplicada por `PermisoRequeridoMixin` (web) y `PermisoPorRol` (API).
- **Espejo de grupos**: cada `Rol` se refleja como un `auth.Group` con los permisos de Django correspondientes (`apps/cuentas/grupos.py`). Un `post_save` del rol crea/actualiza el grupo; un `post_save` del usuario lo deja en el grupo de su rol; un `post_migrate` garantiza los grupos en cualquier entorno. Sin migración de modelos: `Group` y `Permission` son de Django.
- En la ficha de usuario se muestra el **grupo** asignado (evidencia en la revisión).

## 6. Guion de demostración presencial

1. Iniciar sesión con un perfil Administrador; mostrar el dashboard y el menú completo.
2. Cerrar sesión e iniciar con un perfil Administrativo; mostrar que el menú y el dashboard se reducen y que una URL no permitida devuelve 403.
3. Recuperación de contraseña: solicitar, abrir el correo, usar el enlace, fijar la nueva contraseña y entrar con ella.
4. Mantenedor: crear, buscar, editar, desactivar/reactivar y eliminar (p. ej. Vecinos).
5. Transacción: registrar una atención buscando al vecino, eligiendo tipo y sub atención (con validación) y verla en el listado.
6. Usuarios: crear una cuenta, asignarle rol (y cargo) y mostrar el grupo resultante en la ficha.
7. Admin de datos: mostrar que todo lo anterior se hizo por plantillas.

## 7. Evidencias por entregable

- **Aplicación operativa** en AWS EC2 (acceso por navegador).
- **Repositorio GitHub** con `.gitignore`, README e historial de commits.
- **Documento técnico**: este documento + `documentacion/documento_tecnico.md` (modelo de datos, RBAC, API) y `documentacion/descriptor_cargos_delegaciones.md`.
- **Evidencia de IA**: `documentacion/prompts.md` (prompts y uso).
- **Capturas**: login, recuperación, los tres dashboards, una vista de mantenedor y la transacción de atención.

Nota operativa: para la demo real de recuperación por correo, configurar un backend SMTP real en `.env`; en la verificación se usa el backend de consola.
