# PLAN.md — rector de `abstergo`

Fuente única de lo que **falta** en el proyecto y de cómo se verifica.
La especificación de lo que **debe** hacer vive en `documentacion/vision.md`;
este documento no la repite, la enlaza.

## Big picture
- Sistema de gestión para una organización chilena que hoy trabaja en Excel: atención ciudadana municipal.
- Objetivo: reemplazar el Excel por una app web + Android, legible y amigable.
- La app **no está hecha**: es un esqueleto parcial que cumple una fracción de los requisitos del usuario.
- Todo proyecto de este tipo tiene la misma forma: **esqueleto** (invariante) → **módulos** (variable) → **front** (presentación).
- El esqueleto se cierra una vez con un agente; los módulos se paralelizan; el front consume el contrato.

## 1. El esqueleto (invariante)
Test para separar: ¿esto estaría en cualquier proyecto de este tipo? Si sí, es esqueleto.

- **Config por entorno** `config/settings/{base,dev,prod}.py`, todo desde env, sin secretos. — **ausente**.
- **Usuario propio** desde la migración 1, identidad única, `USERNAME_FIELD`. — **hecho** (`cuentas.Usuario`).
- **Autenticación**: sesión web + token con refresh para móvil, endpoints login/refresh/logout y `/me`. — **hecho** (JWT con refresh y blacklist; falta HTTPS).
- **RBAC centralizado**: roles como dato (`Rol.codigo`) + una matriz rol × permiso + un mixin o clase que la aplica. — **hecho** (`apps/common/permisos.py`; web y API la consultan).
- **Validación en el borde**: validadores de campo + cruce en serializer/form + restricciones en la base. — **parcial** (serializers en la API; faltan restricciones en la base).
- **Errores uniformes** 400/401/403/404/500. — **ausente**.
- **Auditoría central** por señal o middleware. — **parcial y mal ubicada** (se llama desde las vistas).
- **Borrado lógico** con un solo significado. — **parcial** (front lógico, admin `DELETE`).
- **Migraciones** versionadas + `makemigrations --check` en CI. — **hecho** (chequeo en `scripts/verificar.sh` y en CI).
- **Seeding idempotente y no destructivo**. — **parcial** (`cargar_datos` resucita borrados).
- **Listados**: paginación, filtro y búsqueda como base. — **hecho**.
- **Verificación**: lint + tests + `check --deploy` en un script y en CI. — **parcial** (script y CI listos; faltan lint y tests).

## 2. Requisitos del usuario → estado
- El hueco de raíz: no existe una lista de requisitos con estado. Eso es "no hay puntos claros de qué cubrir".
- Cada requisito tiene estado y un criterio de aceptación verificable.
- R1 · Login y recuperación con OTP — **hecho**.
- R2 · Roles y permisos aplicados de verdad — **hecho** (web y API, con el menú filtrado por rol).
- R3 · Gestión de usuarios, roles, delegaciones, catálogos y vecinos — **hecho** (CRUD web y de API).
- R4 · Flujo "crear atención" con historial del vecino — **parcial**.
- R5 · Reemplazar el Excel: importación única, export y UX del funcionario — **parcial**.
- R6 · Cumplimiento Ley 21.719 (ARCOP, consentimiento, retención, incidentes, auditoría) — **ausente** (solo modelos).
- R7 · API para el cliente Android — **parcial** (API v1 con token, CRUD y recuperación; falta HTTPS).
- R8 · Dashboard por rol — **parcial**.
- R9 · Seguridad de producción (HTTPS, rate limiting) — **ausente**.
- R10 · Calidad (tests, CI) — **parcial** (CI creada; tests pendientes).

## 3. Módulos (variable, paralelizable)
- Un módulo = una entidad de dominio: modelo, migración, serializer/form, vista, permiso, tests, import/export.
- Se cuelgan del esqueleto y se pueden repartir entre agentes.
- Lista: usuarios/roles, delegaciones, metas, tipos y sub-atenciones, vecinos, atenciones, y las tablas de cumplimiento.

## 4. Front
- Web: existe (plantillas + framework institucional).
- Android: no existe; arranca cuando exista el OpenAPI, que ya está servido en `/api/schema/`.

## 5. Ajustes y cambios (segundo carril)
- Todo cambio, sea módulo o ajuste, **declara qué requisito toca**.
- Ajuste interno (UI, texto, refactor, bug): no toca la matriz; lleva test y bitácora.
- Cambio de comportamiento: actualiza la spec y el documento técnico.
- Sin este carril, cada arreglo de una línea parece exigir el aparato completo.

## 6. Mapa de documentación (quién manda en qué)
- `documentacion/vision.md` = qué **debe** hacer. Cambia si cambia el comportamiento.
- `PLAN.md` = qué **falta** (requisitos + estado + checkpoints). Cambia si un requisito cambia de estado.
- `documentacion/documento_tecnico.md` = qué **hace hoy**. Cambia en todo cambio real.
- `AGENTS.md` = **cómo** se opera. Cambia si cambian comandos o flujo.
- `documentacion/prompts.md` = **evidencia**. Cambia si el prompt es entregable.
- Regla: un ajuste de UI toca "qué hace hoy"; un cambio de negocio toca "qué debe" y "qué hace".

## 7. Método de prompting
- **Verificación antes que confianza**: cada trabajo trae un check binario que cierra el lazo solo.
- **Explorar → planear → implementar → validar**.
- **Contexto mínimo y de alta señal**: el archivo de reglas es corto; lo largo va en skills que cargan a demanda.
- **Determinista vs advisory**: lo que debe pasar siempre va en hooks y CI, no en texto.
- **Subagentes** para investigar y para revisar; el que revisa no es el que escribió.
- **Plantilla de prompt**: qué cambia, qué requisito toca, qué documento actualiza, y qué **no** tocar.

## 8. Frontera de paralelismo (agentes)
- Esqueleto: **serializado**, un agente. Paralelizar ahí colisiona.
- Módulos: paralelizables, cuelgan del esqueleto.
- Front: arranca cuando el contrato existe.
- Esa es la frontera correcta, no el tamaño del trabajo.

## 9. Orden de ejecución
- Cerrar el esqueleto: config por entorno, HTTPS, RBAC en la web, validación y errores uniformes, auditoría central, lint y tests.
- Construir los módulos que faltan: atención, Excel→app, cumplimiento operativo.
- Front Android sobre el OpenAPI de `/api/schema/`.
- Seguridad de producción y calidad continua.

## 10. Bitácora
- `PLAN.md`, `scripts/verificar.sh`, `pyproject.toml` y CI: creados.
- API v1 (`apps/api`): auth JWT, permisos por rol, CRUD con borrado lógico y recuperación por correo (`RecuperacionPassword`). Esquema en `/api/schema/`. Verificado con `scripts/verificar.sh` (EXIT=0, recuperación de punta a punta).
- Permisos por rol en `apps/common/permisos.py` (matriz rol × módulo), aplicados en la web, la API y el menú. Usuario de MariaDB con contraseña rotada.
- Pendiente inmediato de documentación: `documentacion/documento_tecnico.md` (sección de API y permisos) y `.env.example` (variables de JWT y paginación).

## 11. Verificación
- Cada ítem del esqueleto tiene estado (hecho / parcial / ausente).
- Cada requisito tiene estado y un criterio de aceptación verificable.
- Este documento no repite `vision.md`; la enlaza.
- Prueba del lazo: romper `scripts/verificar.sh` debe hacerlo fallar y, con el hook, bloquear el cierre del turno.
