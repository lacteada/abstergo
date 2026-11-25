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
- Principio rector del código: **simplicidad primero** — la menor complejidad, POO con responsabilidad única, DRY (una sola fuente por regla) y documentación corta y fácil de dibujar. El detalle está en `AGENTS.md` §11.

## 1. El esqueleto (invariante)
Test para separar: ¿esto estaría en cualquier proyecto de este tipo? Si sí, es esqueleto.

- **Config por entorno** `config/settings/{base,dev,prod}.py`, todo desde env, sin secretos. — **ausente**.
- **Usuario propio** desde la migración 1, identidad única, `USERNAME_FIELD`. — **hecho** (`cuentas.Usuario`).
- **Autenticación**: sesión web + token con refresh para móvil, endpoints login/refresh/logout y `/me`. — **hecho** (JWT con refresh y blacklist; falta HTTPS).
- **RBAC centralizado**: roles como dato (`Rol.codigo`) + una matriz rol × permiso + un mixin o clase que la aplica. — **hecho** (`apps/common/permisos.py`; web y API la consultan). Desde 2026 suma una segunda matriz **cargo × módulo** (`Cargo`, `MATRIZ_CARGO`): el rol es el acceso y el cargo el puesto funcional, y el permiso se resuelve por unión. Cada rol se refleja además como `auth.Group` espejo (`apps/cuentas/grupos.py`).
- **Validación en el borde**: validadores de campo + cruce en serializer/form + restricciones en la base. — **parcial** (serializers en la API; faltan restricciones en la base).
- **Errores uniformes** 400/401/403/404/500. — **parcial** (páginas 403/404/500 propias; la API responde 400/401/403).
- **Auditoría central** por señal o middleware. — **parcial y mal ubicada** (se llama desde las vistas).
- **Borrado lógico** con un solo significado. — **parcial** (front lógico, admin `DELETE`).
- **Migraciones** versionadas + `makemigrations --check` en CI. — **hecho** (chequeo en `scripts/verificar.sh` y en CI).
- **Seeding idempotente y no destructivo**. — **parcial** (`cargar_datos` resucita borrados).
- **Listados**: paginación, filtro y búsqueda como base. — **hecho**.
- **Verificación**: lint + tests + `check --deploy` en un script y en CI. — **parcial** (script y CI en verde con `ruff` y 131 pruebas; falta `check --deploy` en CI).

## 2. Requisitos del usuario → estado
- El hueco de raíz: no existe una lista de requisitos con estado. Eso es "no hay puntos claros de qué cubrir".
- Cada requisito tiene estado y un criterio de aceptación verificable.
- R1 · Login y recuperación con OTP — **hecho**.
- R2 · Roles y permisos aplicados de verdad — **hecho** (web y API, con el menú filtrado por rol).
- R3 · Gestión de usuarios, roles, cargos, delegaciones, catálogos y vecinos — **hecho** (CRUD web y de API; los cargos salen del descriptor de funciones de las Delegaciones, versión 2026).
- R4 · Flujo "crear atención" con historial del vecino — **parcial**.
- R5 · Reemplazar el Excel: importación única, export y UX del funcionario — **parcial**.
- R6 · Cumplimiento Ley 21.719 (ARCOP, consentimiento, retención, incidentes, auditoría) — **parcial** (modelos implementados; gestión solo por Admin).
- R7 · API para el cliente Android — **parcial** (API v1 con token, CRUD y recuperación; falta HTTPS).
- R8 · Dashboard por rol — **parcial**.
- R9 · Seguridad de producción (HTTPS, rate limiting) — **parcial** (HSTS/cookies/rate limit opt-in con `PRODUCCION_SEGURA=1`; falta TLS efectivo).
- R10 · Calidad (tests, CI) — **hecho** (CI en verde; **131 pruebas** con `pytest` y `ruff`, registro en `documentacion/pruebas.md`).

## 3. Módulos (variable, paralelizable)
- Un módulo = una entidad de dominio: modelo, migración, serializer/form, vista, permiso, tests, import/export.
- Se cuelgan del esqueleto y se pueden repartir entre agentes.
- Lista: usuarios/roles, cargos de delegación, delegaciones, metas, tipos y sub-atenciones, vecinos, atenciones, organizaciones comunitarias, la matriz SGR (períodos, áreas, indicadores, metas, registros) y el tubo de trabajo (kanban), y las tablas de cumplimiento.

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
- **Segunda evaluación**: `estado` y `codigo` en los catálogos (`ConEstado`, migración de datos `catalogos.0004`), multi-delegación (`Usuario.delegaciones_autorizadas`), contexto de delegación en la cabecera con selector (`apps/common/delegaciones.py`), acotado de listados y formularios al alcance del perfil, vista de consulta en los CRUD (`ConsultaBase`), dependencia Tipo → Sub Atención con validación en servidor, identificador de atención, estados de interfaz y espera entre reenvíos del código (`OTP_REENVIO_SEGUNDOS`). Pruebas en `conftest.py` y `apps/*/tests.py`; registro en `documentacion/pruebas.md`; carga con `scripts/estres.py`; despliegue en `documentacion/despliegue_aws.md`.
- **2026-11-13 · Módulos SGR, organizaciones y tubo**: apps nuevas `apps/comunidad` (juntas de vecinos y agrupaciones, CRUD + API, sin importar aún los 2.709 registros), `apps/sgr` (períodos, áreas, indicadores, metas, registros, reclamos/felicitaciones y ajuste de días; cálculo puro en `calculos.py`, reglas del 4° trimestre y tablero con semáforo) y `apps/tubo` (kanban de tareas por delegación, visible al delegado). Se suman las claves de permiso `community`, `sgr`, `sgr_records`, `sgr_adjustments` y `tasks`; `Cargo.funciones` con el descriptor 2026; `SubAtencion.forma` y las sub atenciones del gestor social; y la Delegación **Alfalfares**. Actualizados `documento_tecnico.md` (§20) y `scripts/verificar.sh`.
- **2026-11-13 · Cierre de brechas SGR, bloque 1 (P1)**: `Periodo` con `situacion` y topes/umbrales configurables; `Indicador` con cargo/tipo de cálculo/requiere evidencia; `MetaIndicador` con sobrescritura por funcionario; `RegistroGestion` con etapa, tipo de solicitante, contacto, `puntua`+motivo y estado; reglas C1/C2/C5 en `validaciones.evaluar_puntaje`; `Evidencia` + `Validacion` + módulos `evidence`/`validation` (quien registra no valida); `Ausencia` con rango que descuenta la meta al día (tope 100 %). Migraciones `sgr/0002`, `sgr/0003` y `sgr/0004`. Contracto de API ampliado (`evidence`, `validations`, `sgr-absences`).
- **2026-11-15 · Cierre de brechas SGR, bloque 2**: RF-050 (`Llamada` en `apps/casos` + señal desde `Atencion` + cierre), RF-054 (`Carta` en `apps/tubo` con totales por estatus), RF-055 (vista `Agenda` del delegado con export). RN-001 (excepción de ponderadores + advertencia en tablero), RF-030 (actividad reciente en la ficha), RN-017/018/019 parametrizados (`validaciones.py`). `consulta` pasa a leer tableros e informes; coordinador con alcance global (según la spec SGR §2). RNF-009 (límites de evidencia), RNF-005/R9 (HTTPS/HSTS y rate limit de login) y RNF-015 (páginas de error). Migraciones `casos/0004`, `tubo/0005`, `sgr/0010`. Verificación: 118 pruebas, 0 fallos.
- **2026-11-23 · Rediseño del tablero del tubo (RF-021)**: `tubo/tablero.html`
  suma la fila de cuatro KPI y tarjetas con código de color por estado (gris,
  rojo, ámbar, verde) y documento vinculado; `Tablero` calcula los KPI y
  `ACCION_SIGUIENTE` + `TareaTubo.accion_destino` (`apps/tubo/models.py`) dan el
  paso siguiente del flujo; el botón y la reasignación van por `tubo.js`. Ajuste
  de UI: actualiza `documento_tecnico.md` §20.3.
- **2026-11-23 · Buzón de trabajo (RF-021/037)**: nueva vista `/buzon/`
  (`panel:buzon`, `BuzonTrabajo`) que reúne el trabajo accionable de todos los
  módulos que el perfil puede leer —compromisos abiertos, actividades por
  corregir, evidencias por validar, llamadas y alertas—, agrupado por importancia
  (crítico/alto/medio/bajo) y con enlace al detalle y a la trazabilidad. Lógica en
  `apps/panel/servicios.py::buzon`; ámbito global por rol vía `acotar`. Enlace en
  el menú "Trabajo" y en las acciones del panel. Documentación: §7 y §13.1.
- **2026-11-23 · Tablero SGR legible (RF-029)**: las cifras crudas (logrado y
  meta al día) se reemplazan por una **barra de avance** (relleno = logrado,
  marca vertical = meta al día) y un **cumplido** en % (logrado ÷ meta al día,
  100 % = al día), con los valores crudos en el `title` de cada celda.
  `calculos.relativo` es el cálculo puro; `servicios.resumen_area`,
  `resumen_por_cargo` y los totales exponen `relativo` y `promedio_esperado`, y
  el total se normaliza por el número de áreas. Cambia `tablero.html`,
  `global.html`, el pie de `personal.html` y `institucional.css`
  (`.avance`, `.cumplido`). Actualiza `documento_tecnico.md` §20.1.
- **2026-11-23 · Revisión de seguridad y coherencia**: cierre de los hallazgos de
  los tres cambios paralelos. (1) **Acotamiento territorial en todas las
  operaciones**, no solo el listado: `AcotadoMixin` (web) y `BaseViewSet` (API)
  filtran por delegación en ver/editar/borrar/acciones, con la ruta del campo
  resuelta por modelo (`delegaciones.campo_delegacion_de`), y las vistas custom
  (Crear Atención, cierre de llamada, kanban) también. (2) **RN-010 en una sola
  fuente** (`validaciones.falta_evidencia`), compartida por form y serializer, y
  `Evidencia.clean` acepta archivo **o** vínculo. (3) **`model.clean()` en la
  API** (`LimpiaModeloMixin`) y validadores del modelo repuestos en campos
  redeclarados. Verificación: `scripts/verificar.sh` en verde (124 pruebas).
  Actualiza `documento_tecnico.md` §19.1, §20.1 y §23.
- **2026-11-23 · Ajustes de UI**: se **retira el buzón de trabajo** (`/buzon/`,
  vista, servicio, plantilla, menú y CSS); el **kanban de compromisos** resalta
  las tareas atrasadas (fondo rojo, distintivo «Atrasada · N días» y conteo por
  columna); y todos los **listados** suman un selector de filas por página
  (8/16/32/64, `?por=`, 8 por defecto). Actualiza `documento_tecnico.md` §7,
  §13.1, §20.3 y §24 y `vision.md` §6.3.
- **2026-11-23 · Cartas, automatización y directiva**: se **repone el tubo de
  cartas** en el menú («Cartas», con baja lógica y reactivación); cada
  **atención crea automáticamente un compromiso** en el tubo de su delegación
  (`apps/tubo/signals.py`); y `Organizacion` suma la **directiva** (presidente,
  tesorero, secretario) en modelo, formulario, API y ficha. Migración
  `comunidad/0003`. Actualiza `documento_tecnico.md` §20.2, §20.3 y §25.
- **2026-11-23 · Tabla y kanban, alternables**: compromisos y cartas se ven en
  **tabla y en kanban**, con un botón para alternar («Ver en kanban» / «Ver en
  tabla»). Compromisos: `/tubo/` (kanban) y `/tubo/tareas/` (tabla); cartas:
  `/tubo/cartas/` (tabla) y `/tubo/cartas/kanban/` (kanban, arrastre y botón
  Aprobar/Finalizar vía `CartaMover`). El CRUD completo queda en la tabla.
  Actualiza `documento_tecnico.md` §20.3 y §25.
- **2026-11-23 · Flujo y usabilidad**: buscador en todos los campos de lista
  (autocompletado central), **calendario** en las fechas (flatpickr local), **modales
  que no se cierran al clic fuera**, acciones de fila como **botones**, **directiva
  como vecinos reales** (presidente/tesorero/secretario pasan a FK de `Vecino`, con
  creación en el mismo formulario), **paso manual al tubo** (se retira la
  automatización; botón «Enviar al tubo» en atención/carta/actividad), **kanban con
  drag&drop y orden persistente sin recarga**, **cartas con tipo**
  (felicitación/regaño), **período activo en la top bar**, **tablero SGR en el
  dashboard** y **mantenedores plegados**. Migraciones `comunidad/0004`, `tubo/0006`
  y `tubo/0007`. Actualiza `documento_tecnico.md` §26, `vision.md` §6.6 y §25.

- **2026-11-24 · Auditoría y completitud**: se crea `documentacion/auditoria/` con `INFORME_DETALLE_ABSTERGO.md` (cobertura RF ~95 %, RNF ~75 %), `PROMPT_DETALLE_ABSTERGO.md` (regenerable) y `ROADMAP_COMPLETITUD_ABSTERGO.md` (qué falta para una app completa, P1–P3). Se corrige el desfase de este PLAN (§1 y §2) y de `pruebas.md`. Verificación: 131 pruebas, 0 fallos; `check --deploy` da 7 issues con `PRODUCCION_SEGURA` apagado y 3 con `=1`.

- **2026-11-24 · Rediseño de formularios y UX (Fase A)**: los 22 formularios agrupan sus campos en filas (`FormularioCRUD.filas`/`distribucion`); la directiva de `OrganizacionForm` es un selector de persona con buscador y alta inline (`SelectorPersona` + `personas.js`); fechas nativas con calendario (`CampoFecha`/`CampoFechaHora`), multiselect con búsqueda (`SelectMultipleBuscable` + `multibuscable.js`), teléfono con teclado numérico; accesibilidad (`:focus-visible`, `aria-invalid`/`aria-describedby`, `<title>` por pantalla, contraste) y menú off-canvas. Verificación: 131 pruebas, 0 fallos, ruff limpio. Detalle en `documentacion/auditoria/INFORME_UX_ABSTERGO.md` y `REDISENO_ANTES_DESPUES.md`.

- **2026-11-24 · Navegación y kanban (Fases B y C)**: una sola fuente de menú (`apps/common/menu.py`) alimenta el sidebar y el panel; las acciones del panel se filtran por la matriz de módulos (sin enlaces que terminen en 403 — se quitó el "Tablero de delegación" del delegado). El kanban usa Pointer Events: marcador de destino, animación FLIP, sin recarga de página, soporte táctil y arrastre solo con permiso de escritura (`data-escribir`). Se suman migas, visor de evidencia en la ficha y estado de envío del botón de guardar. Verificación: 131 pruebas, 0 fallos, ruff limpio.

## 11. Verificación
- Cada ítem del esqueleto tiene estado (hecho / parcial / ausente).
- Cada requisito tiene estado y un criterio de aceptación verificable.
- Este documento no repite `vision.md`; la enlaza.
- Prueba del lazo: romper `scripts/verificar.sh` debe hacerlo fallar y, con el hook, bloquear el cierre del turno.


## Seguridad y calidad demostrables del 25 de noviembre de 2026
Base de trabajo: origin/main 164eef7. No se trasladan automáticamente los dos commits locales anteriores, porque el usuario declaró al repositorio remoto como fuente actual.

- RNF-003/R9: segundo factor TOTP optativo por cuenta, con alta confirmada por contraseña y código, QR generado localmente, semilla cifrada mediante Fernet y ocho recuperaciones con hash de un solo uso. Clave independiente MFA_ENCRYPTION_KEY. Bloqueo persistente de cinco minutos tras cinco fallos; rechazo de pasos TOTP ya consumidos. No hay generación de códigos en la pantalla de acceso.
- La web crea la sesión solo después del factor. El acceso alternativo del Admin redirige al flujo general. API login admite otp cuando la cuenta tiene MFA; JWT, refresh y sesiones API comprueban la versión de la credencial. Altas y bajas invalidan credenciales anteriores; cambios de contraseña revocan JWT mediante CHECK_REVOKE_TOKEN.
- Registro privado de activación, desactivación, rechazos, bloqueos y accesos del propio usuario. Nunca guarda contraseñas, semillas ni códigos. Las páginas sensibles llevan no-store. La baja exige contraseña más TOTP o recuperación.
- Corrección de aislamiento: si un perfil territorial no tiene delegación autorizada, acotar devuelve un queryset vacío. Conserva el alcance global de admin/coordinador.
- Calidad: /calidad/ solo para admin/coordinador, accesible desde el menú. Consume un reporte JSON firmado, verifica la huella del código, muestra ejecución, revisión, duración, pruebas y fallos; rechaza contenido alterado y advierte diferencias de código o antigüedad. No ejecuta comandos desde HTTP ni inventa resultados.
- scripts/verificar_calidad.py ejecuta check, comprobación/aplicación de migraciones, carga de catálogos, Ruff, pytest/JUnit, pip-audit y el bloque smoke oficial sobre SQLite temporal. Requiere requirements-dev.txt. Logs y reportes en var/ (ignorado). La firma usa SECRET_KEY del entorno que mostrará el reporte; la evidencia de CI se conserva como artefacto y debe regenerarse con la configuración del destino antes de publicarse en ese panel.
- Criterios seleccionados del modelo ISO/IEC 25010:2023: adecuación funcional (flujos y validaciones), fiabilidad (regresión y migraciones), mantenibilidad (análisis estático y comprobación reproducible) y seguridad (MFA, permisos, CSRF y revocación). Es una evaluación parcial del producto, no una certificación ni conformidad integral con ISO.
- Migración cuentas/0009: SegundoFactor y EventoAcceso. Los usuarios existentes siguen sin MFA hasta vincular un autenticador. No existe un reinicio de MFA por correo ni una puerta de omisión; conservar recuperaciones y respaldar la llave. Producción necesita HTTPS válido, reloj sincronizado, DEBUG=False y caché compartida para el límite general por IP. La comprobación --deploy incorpora cuentas.E001 si falta una llave MFA válida.


### Verificación observada de seguridad y calidad
148 pruebas aprobadas, cero fallos y errores. Ocho comprobaciones aprobadas, incluida auditoría de dependencias sin vulnerabilidades conocidas y smoke oficial. Validación visual del desafío, rechazo de código, acceso válido, estado de MFA y panel; descarga JSON comprobada. Evidencias en documentacion/evidencias/seguridad_calidad y guía en documentacion/seguridad_calidad.md. Bash no ejecutado en Windows: descarga/ejecución de Git portable rechazada por revisión automática; se ejecutó la puerta Python y el mismo bloque smoke original. Implementación f5e4570 publicada en main con Demiannnn18; GitHub Actions 45665505999 aprobó Bash, evidencia de calidad y artefactos con 148 pruebas. Se actualiza upload-artifact a v7.0.2 para retirar el aviso de Node 20. AWS sigue pendiente por falta de llave SSH.
