# Registro de pruebas — Segunda evaluación

Sistema Municipal de Gestión de Atención Ciudadana (Abstergo).
Acompaña a los requisitos del PDF de la segunda evaluación.

- Fecha de la corrida: _(completar al cerrar la entrega)_
- Responsable: _(integrante que ejecuta)_
- Entorno funcional: SQLite temporal vía `scripts/verificar.sh` (Air/Dev).
- Entorno de carga: AWS (EC2 + Apache + gunicorn + MariaDB).

## 1. Pruebas automáticas (funcionales y unitarias)

Se ejecutan con `bash scripts/verificar.sh`, que corre `check`, migraciones,
`cargar_datos`, `ruff` y `pytest`. Cada caso es un test en el repositorio.

| # | Requisito | Módulo | Precondiciones | Resultado esperado | Estado | Evidencia |
|---|---|---|---|---|---|---|
| 1 | Login y recuperación | cuentas | Usuario activo con correo | Flujo completo cambia la contraseña; el código sirve una vez | Aprobado | `apps/cuentas/tests.py` |
| 2 | Recuperación — reenvío | cuentas | Código recién pedido | El reenvío respeta la espera; emite al vencer | Aprobado | `apps/cuentas/tests.py` |
| 3 | Permisos por rol | common | Roles del sistema | La matriz concede y niega como corresponde | Aprobado | `apps/common/tests.py` |
| 4 | Listados — alcance | ciudadanos | Usuario acotado a una delegación | Solo ve los registros de su delegación | Aprobado | `apps/common/test_web.py` |
| 5 | Listados — alcance global | ciudadanos | Rol admin/coordinador | Ve todas las delegaciones | Aprobado | `apps/common/test_web.py` |
| 6 | Listados — búsqueda | ciudadanos | Registros cargados | Coincidencia parcial, sin distinguir mayúsculas | Aprobado | `apps/common/test_web.py` |
| 7 | Listados — exportar Excel | ciudadanos | Registros y filtro `q` | El `.xlsx` respeta el filtro y no exporta campos internos | Aprobado | `apps/common/test_web.py` |
| 8 | CRUD — consultar | ciudadanos | Registro existente | La ficha muestra los datos del registro | Aprobado | `apps/common/test_web.py` |
| 9 | CRUD — crear con código/estado | catalogos | Rol con escritura | Guarda código y estado; el código es obligatorio | Aprobado | `apps/catalogos/tests.py` |
| 10 | CRUD — delegación autorizada | catalogos | Rol acotado a una delegación | Rechaza una delegación no autorizada en el servidor | Aprobado | `apps/catalogos/tests.py` |
| 11 | Ingreso de atención | atenciones | Vecino y catálogos | Registra la atención y muestra el identificador | Aprobado | `apps/atenciones/tests.py` |
| 12 | Tipo → Sub Atención | atenciones | Tipo y subatención de otro tipo | Rechaza la subatención que no pertenece al tipo | Aprobado | `apps/atenciones/tests.py` |
| 13 | Contexto de delegación | panel | Usuario con varias delegaciones | El cambio actualiza el alcance de los listados | Aprobado | `apps/panel/tests.py` |
| 14 | Contexto — rechazo | panel | Delegación no autorizada | El servidor no cambia el contexto | Aprobado | `apps/panel/tests.py` |

Comando:

```bash
cd ~/code/ina/backend/abstergo
bash scripts/verificar.sh        # espera VERIFICACIÓN OK
```

Resultado de la última corrida: **25 pruebas, 0 fallos**.

## 2. Pruebas manuales de interfaz

Complementan a las automáticas; se ejecutan en la URL AWS con acceso de
evaluación.

| Requisito | Precondición | Pasos | Esperado | Estado |
|---|---|---|---|---|
| SweetAlert2 | Sesión con escritura | Dar de baja un registro y cancelar; luego confirmar | Pide confirmación; avisa el resultado; no muestra éxito si falla | Aprobado |
| Modal del CRUD | Sesión con escritura | "Nuevo" en un mantenedor, guardar con error y luego corregir | El error se ve en el formulario; al guardar refresca el listado | Aprobado |
| Distintivo de delegación | Sesión con perfil | Abrir la cabecera | Muestra código, nombre, usuario y rol; icono y texto, no solo color | Aprobado |
| Selector de contexto | Perfil multi-delegación | Cambiar de delegación y editar con cambios sin guardar | Advierte antes de cambiar; actualiza listados y filtros | Aprobado |
| Estados de listado | Sesión con lectura | Buscar sin coincidencias y dejar vacío | Distingue "sin coincidencias" de "aún no hay registros" | Aprobado |
| Sub Atención dependiente | Sesión con escritura | Elegir tipo y ver la segunda lista; cambiar tipo | Solo muestra las subatenciones del tipo; limpia la no válida | Aprobado |

## 3. Pruebas de estrés

Herramienta: `scripts/estres.py` (biblioteca estándar, sin dependencias nuevas).
Entorno: AWS (EC2 + Apache + gunicorn + MariaDB).

Umbrales definidos de antemano (en el propio script):

- Latencia percentil 95 ≤ 1500 ms.
- Tasa de error ≤ 1 %.

Escenario: petición `GET /login/` (estática + render) subiendo la concurrencia.

```bash
python scripts/estres.py --url <URL_AWS> --ruta /login/ \
    --niveles 5,10,20,40 --duracion 20 --salida documentacion/pruebas.md
```

_(la tabla de resultados se anexa al final de este documento al ejecutar el
script sobre el entorno desplegado)_

## 4. Defectos y correcciones

| # | Defecto | Corrección | Estado |
|---|---|---|---|
| 1 | El rol global quedaba acotado por su delegación principal | `activa()` devuelve "todas" salvo elección explícita | Corregido y probado |

## 5. Pendientes por falta de Backend

No quedan pantallas sin persistencia. Todos los mantenedores, el ingreso de
atención y el flujo de acceso persisten en MariaDB. Lo que no cubre esta
entrega: las tareas trimestrales y el módulo de Reportes (fuera de alcance en
`documentacion/vision.md`).
