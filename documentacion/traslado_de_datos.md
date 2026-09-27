# Traslado de datos — Evaluación 1 a Evaluación 2

De archivos JSON a base de datos relacional.

## 1. Origen

- Proyecto de la Evaluación Sumativa 1: `~/code/ina/backend/Abstergo2`.
- Almacenaba en archivos JSON, sin base de datos ni ORM.
- Se lee en modo lectura. No se modifica ni se reutiliza su código.

## 2. Archivos de origen

| Archivo | Filas | Destino |
|---|---|---|
| `apps/usuarios/data/usuarios.json` | 6 | `usuarios.json` y `roles.json` |
| `apps/delegacion/data/delegaciones.json` | 6 | `delegaciones.json` |
| `apps/agenda/data/compromisos.json` | 8 | sin destino |
| `apps/actividades/data/actividades.json` | 100 | sin destino |

Campos de cada archivo de origen:

- **usuarios.json:** `id`, `nombre`, `email`, `rol`, `delegacion`, `cargo`, `activo`, `avatar_color`.
- **delegaciones.json:** `codigo`, `nombre`, `territorio`, `encargado`, `enfasis`, `imagen`.
- **compromisos.json:** `codigo`, `solicitante`, `territorio`, `responsable`, `fecha_compromiso`, `fecha_limite`, `estado`, `observacion`, `historial`.
- **actividades.json:** `codigo_evidencia`, `fecha`, `descripcion`, `accion`, `contacto`, `telefono`, `delegacion`, `estado`, `fecha_creacion`.

## 3. Esquema nuevo

7 tablas, con las llaves foráneas en `PROTECT` y sin borrados en cascada.

| Tabla | Campos | Relación |
|---|---|---|
| `organizacion_delegacion` | codigo, nombre, direccion, comuna, activo, eliminado | — |
| `cuentas_rol` | nombre, descripcion, eliminado | — |
| `cuentas_perfilusuario` | usuario, rol, delegacion, estado | → Rol, → Delegacion |
| `catalogos_meta` | nombre, descripcion | — |
| `catalogos_tipoatencion` | nombre, descripcion, eliminado | — |
| `catalogos_subatencion` | nombre, tipo_atencion | → TipoAtencion |
| `ciudadanos_vecino` | nombre, rut, direccion, telefono, territorio, tipo_gestion, estado | → Delegacion |

## 4. Mapeo campo por campo

### Delegaciones

| Origen | Destino | Tratamiento |
|---|---|---|
| `codigo` | `codigo` | directo, es la llave de búsqueda |
| `nombre` | `nombre` | directo |
| — | `direccion` | se agrega |
| — | `comuna` | se agrega, siempre "La Serena" |
| — | `activo` | se agrega, `true` |
| `territorio` | — | descartado |
| `encargado` | — | descartado |
| `enfasis` | — | descartado |
| `imagen` | — | descartado |

### Roles

El origen no tiene un archivo de roles: el rol viene como texto en cada usuario. Se generan los 6 distintos.

| Origen | Destino | Tratamiento |
|---|---|---|
| `usuarios[].rol` | `nombre` | los 6 valores distintos |
| — | `descripcion` | se escribe |

Valores: ADMIN, COORDINADOR, DELEGADO, FUNCIONARIO, VERIFICADOR y CONSULTA.

### Usuarios

| Origen | Destino | Tratamiento |
|---|---|---|
| `nombre` | `first_name` y `last_name` | se parte por el primer espacio |
| `email` | `username` y `email` | directo, es la llave de búsqueda y el login |
| `rol` | `PerfilUsuario.rol` | por referencia al nombre del rol |
| `delegacion` | `PerfilUsuario.delegacion` | por referencia al código |
| `activo` | `PerfilUsuario.estado` | `true` → Activo, `false` → Inactivo |
| — | contraseña | se asigna con `set_password()` desde el `.env` |
| `id` | — | descartado, lo reemplaza la llave primaria |
| `cargo` | — | descartado |
| `avatar_color` | — | descartado |

### Vecinos

| Origen | Destino | Tratamiento |
|---|---|---|
| — | `nombre`, `rut`, `direccion`, `telefono` | datos ficticios |
| `delegaciones[].codigo` | `territorio` | llave foránea a Delegación |
| — | `tipo_gestion` | texto libre, sin entidad propia |
| — | `estado` | Activo o Inactivo |

### Metas, Tipos de Atención y Sub Atenciones

Sin origen. Se llenan con datos ficticios.

- `catalogos_meta` — 6 filas.
- `catalogos_tipoatencion` — 4 filas.
- `catalogos_subatencion` — 8 filas, cada una referenciando su tipo de atención por nombre.

## 5. Lo descartado y por qué

- **compromisos.json, 8 filas.** Compromiso es una entidad de la Evaluación 1 con su propia máquina de estados. No tiene equivalente entre las 7 entidades del diseño, porque el diseño no contempla Compromisos ni Actividades.
- **actividades.json, 100 filas.** Mismo motivo. Es el archivo con más información de la Evaluación 1 y queda fuera.
- **`cargo`, 6 valores.** Un cargo por usuario (Administrador General, Coordinadora del Sistema, Jefe de Delegación Centro, Auxiliar Social, Verificador de Evidencias, Analista de Informes). Modelarlos exigía una octava entidad y una pantalla que el mockup no define, así que se descartan. Consecuencia: la tabla `catalogos_meta` queda sin ninguna relación.
- **`avatar_color`.** Es presentación, no dato.
- **`id`.** Lo reemplaza la llave primaria de Django.
- **`territorio`, `encargado`, `enfasis` e `imagen` de delegaciones.** Los tres últimos son de presentación. El `territorio` descriptivo no tiene destino: el campo `territorio` de Vecino es una llave foránea a Delegación, no un texto.

Efecto del descarte: de 4 archivos de origen se migran 2. La pauta pide una "migración completa desde JSON", y esta decisión la deja parcial. Queda documentada como decisión consciente, tomada en `04_Choques_Requerimientos.md` §13.

## 6. Formato del JSON nuevo

- Vive en `datos_nuevos/`, un archivo por entidad.
- Cada archivo es un arreglo de objetos, con los mismos nombres de campo que las columnas de la tabla.
- Los tres transformados: `delegaciones.json`, `roles.json` y `usuarios.json`.
- Los cuatro escritos a mano: `metas.json`, `tipos_atencion.json`, `sub_atenciones.json` y `vecinos.json`.
- El comando `cargar_datos` recorre los 7 archivos en orden de dependencia —delegaciones y roles, después usuarios, luego los catálogos y al final vecinos— y escribe con `update_or_create`.

## 7. Verificación del traslado

Todo comprobado ejecutando la carga:

- Primera ejecución de `cargar_datos`: **46 registros creados**.
- Segunda ejecución: **0 creados, 46 actualizados**. La carga es idempotente.
- Conteos por tabla: 6 delegaciones, 6 roles, 6 perfiles, 6 metas, 4 tipos de atención, 8 sub atenciones y 10 vecinos.
- Las 7 tablas quedan con registros, no solo las dos con origen.
- Los 7 archivos no traen ninguna llave que no exista como campo en el modelo.
