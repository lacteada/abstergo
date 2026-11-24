# Auditoría de diseño y experiencia (UX) — webapp Abstergo

- Fecha: 2026-11-24.
- Qué audita: el **tramo que recorre el usuario** (entrada → trabajo → salida) y por qué hoy no reemplaza al Excel. No audita requisitos ni cobertura funcional.
- Complementa: `INFORME_DETALLE_ABSTERGO.md` (funcional/seguridad) y `ROADMAP_COMPLETITUD_ABSTERGO.md` (qué falta).
- Evidencia: `archivo:línea`. Toda afirmación se verificó en el código.

> **Estado 2026-11-24.** El rediseño se implementó: formularios en filas (22), selector de persona en la directiva, Fase A (calendarios, buscables, multiselect, accesibilidad), **Fase B** (menú único panel↔sidebar, acciones por módulo, sin enlaces muertos) y **Fase C** (kanban con Pointer Events: marcador, animación, sin recarga, táctil y permiso de escritura), más migas, visor de evidencia y estado de envío. Ver `REDISENO_ANTES_DESPUES.md` y `PLAN.md`. Verificación: 131 pruebas, 0 fallos, ruff limpio.

## 0. Método

- Se recorre la app "como usuario": dónde entra, cuántas pantallas toca, cuántas veces elige entre opciones, y dónde se frena.
- Criterio de "reemplaza al Excel": que la tarea real (registrar una gestión, atender a un vecino, cerrar un compromiso) se haga con menos decisiones y menos pasos que en una planilla.
- Lo que se audita: navegación y visibilidad por rol, formularios e inputs, información por objeto, kanban e interacciones.

## 1. El tramo por rol

- **Funcionario** — entra y ve "Mi jornada" con 8 ítems de menú + 2 mantenedores. Su trabajo es registrar actividad, subir evidencia y ver su tablero, pero el menú le ofrece también mantenedores que no usa.
- **Delegado** — ve "Mi delegación"; su panel incluye un chip **"Tablero de delegación" que apunta a `sgr:tablero` y devuelve 403** (no tiene módulo `sgr`) (`panel/servicios.py:50`, `common/permisos.py:98-101`).
- **Verificador** — el tramo más limpio: 2 ítems (Evidencias, Por validar). Su dashboard es el más pobre: sin resumen ni "últimas".
- **Coordinador** — recibe el **mismo menú de 22 ítems que el admin** (`common/permisos.py`), aunque su panel solo lista 4 acciones y solo escribe metas.
- **Admin** — 22 ítems; sus mantenedores aparecen **duplicados** (panel + sidebar).
- **Consulta** — 4 ítems de trabajo legibles; panel con solo botón + chips.

**Lectura del tramo**
- El menú no refleja el trabajo: se muestran opciones que el rol no puede usar (403) y se ocultan flujos clave detrás de búsquedas.
- Dos fuentes distintas del "qué veo": el sidebar por la matriz de módulos y el panel por una tabla aparte (`panel/servicios.py:37-74`) que no siempre coinciden.

## 2. ¿Reemplaza al Excel? (por tarea real)

- **Registrar una gestión (funcionario)**: `RegistroGestionForm` tiene **20 campos** en un bloque lineal (`sgr/forms.py:75`) → más pesado que escribir una fila en Excel.
- **Atender a un vecino**: el formulario es **inalcanzable sin buscar primero** un vecino; no hay "nueva atención" directa (`templates/partials/crear_atencion.html:108-116`). La búsqueda es por botón (sin autocompletar), a diferencia del resto del sistema.
- **Cerrar un compromiso (delegado)**: depende del kanban, que en cada movimiento **refresca toda la página** (`static/js/tubo.js:50-63`) y en móvil **no responde al arrastre**.
- **Una organización + su directiva (delegado/OROC)**: `OrganizacionForm` pide **22 campos** en una sola columna, con 6 de ellos (2 por cargo) para la directiva.

## 3. Inventario de formularios (ANTES)

**Transversal**
- Todos heredan de `FormularioCRUD` (`common/forms.py:17`), que acota delegación y vuelve buscables los `Select` de FK registradas.
- **Ningún** `DateField`/`DateTimeField` declara `type="date"`: se renderizan `<input type="text">` y `static/js/fechas.js` no los engancha → **fechas a mano**.

**Densidad y problemas por formulario**
| Formulario | Campos | Problemas |
|---|---|---|
| `OrganizacionForm` (`comunidad/forms.py:13`) | 22 | densidad máxima; directiva con 2 campos por cargo; fechas `text` |
| `RegistroGestionForm` (`sgr/forms.py:75`) | 20 | densidad; evidencia y 4 campos de contacto sin agrupar; fechas `text` |
| `TareaTuboForm` (`tubo/forms.py:5`) | 14 | densidad; `atencion` con select plano; fecha `text` |
| `CartaForm` (`tubo/forms.py:28`) | 11 | fecha `text` |
| `PeriodoForm` (`sgr/forms.py:22`) | 10 | umbrales/topes sin contexto; fechas `text` |
| `CasoSocialForm` (`casos/forms.py:5`) | 8 | `caso_anterior` select plano; fecha `text` |
| `UsuarioForm` (`cuentas/forms.py:33`) | 7-8 | `delegaciones_autorizadas` multiselect **sin búsqueda**; `rol` select plano |
| `VecinoForm` (`ciudadanos/forms.py:6`) | 7 | RUT/teléfono sin `inputmode` ni máscara |
| `AtencionForm` (`atenciones/forms.py:25`) | 6 | flujo atado a búsqueda previa |
| `EvidenciaForm` (`sgr/forms.py:171`) | 4 | `registro` select plano; `archivo` requerido aunque el modelo admita solo vínculo |
| `ValidacionForm`/`ComentarioForm` | 3 / 2 | `evidencia`/`registro` select plano |

**Inputs problemáticos (transversales)**
- Multiselect M2M sin buscador: `Usuario.delegaciones_autorizadas` (`cuentas/forms.py:59`); `_buscables()` excluye M2M (`common/forms.py:27-43`).
- Selects planos a modelos no registrados en `common/autocomplete.py`: `Rol`, `Atencion`, `RegistroGestion`, `CasoSocial`, `Evidencia`.
- Teléfono y RUT sin `inputmode`/`pattern`/máscara; único `inputmode` del proyecto es el código OTP (`cuentas/forms.py:111`).
- Sin `fieldset`/`legend`: `partials/formulario.html` pinta todo en una lista plana (`templates/partials/formulario.html:11-19`).

## 4. Información por objeto

**Cómo se declara**
- Columnas del listado: `templates/<app>/<entidad>_lista.html`, bloque `encabezado`.
- Ficha: `consulta_campos` en cada vista (`common/vistas_base.py:381-403`), pintada por `partials/consulta.html`.
- Formulario: `Meta.fields`.

**Desalineaciones (esto es lo que confunde)**
| Entidad | Listado | Ficha | Formulario |
|---|---|---|---|
| Organizacion | 7 | **18** | **22** |
| RegistroGestion | 8 | 11 | **20** |
| TareaTubo | 6 | 15 | 14 |
| Atencion | 6 | 12 | 6 |
| Usuario | 7 | 9 | 8 |
| Indicador | 5 | 5 | 7 (pide campos que la ficha oculta) |
| MetaIndicador | 5 | 5 | 7 |

- Regla de diseño propuesta: **el listado muestra lo que permite decidir**; la ficha muestra lo que se registró; el formulario pide **solo lo necesario** y agrupa el resto en "avanzado".

## 5. Kanban (compromisos y cartas)

**Mecánica actual** (`static/js/tubo.js`)
- HTML5 drag&drop puro; movimiento optimista; persiste por POST `tubo:tareas_mover`/`tubo:cartas_mover`.
- Tras confirmar, **refresca la página completa** y reemplaza `kanban.innerHTML` (`tubo.js:50-63`).

**Problemas**
1. **Sin indicador de destino** ni placeholder en `dragover` (`tubo.js:105-110`).
2. **Sin animación**: la sección del kanban no tiene `transition`/`@keyframes` (`institucional.css:653-782`).
3. **Refresco total** por cada movimiento → parpadeo y pérdida de scroll.
4. **Permisos mal gestionados**: `draggable` siempre activo; un rol de lectura arrastra, el POST da 403 y la tarjeta "salta" (`tubo.js:88-102`); el botón de paso queda deshabilitado sin re-habilitarse (`tubo.js:115`).
5. **Sin soporte táctil** (HTML5 DnD no dispara en touch) → en móvil solo queda el botón de paso.
6. **No accesible por teclado** (sin `aria-grabbed`/alternativa).
7. **Persistencia parcial**: solo renumera la columna destino; las cartas no reordenan (`tubo/views.py:248-264,429-439`).

**Rediseño propuesto**
- Gatear `draggable` por permiso de escritura; en modo lectura, mostrar botones de paso.
- Indicador de destino (gap/placeholder animado) y transición de posición (FLIP o View Transitions API).
- Actualizar solo el DOM afectado, sin refresco total.
- Soporte puntero/táctil y alternativa por teclado (mover con atajos o menú).

## 6. Navegación y visibilidad por rol

- **Dos fuentes del menú**: sidebar por `modulos_lectura` (`common/contexto.py:17`) y panel por `ACCIONES` (`panel/servicios.py:37-74`).
- **Enlaces muertos**: delegado → "Tablero de delegación" (`sgr:tablero` → 403).
- **Exceso**: coordinador con menú de admin (21-22 ítems) aunque su trabajo es acotado.
- **Duplicación**: mantenedores en panel y sidebar para admin.
- **"Últimas atenciones" sin enlace** (`templates/inicio.html:43-55`).

**Rediseño propuesto**
- Una sola fuente de verdad del menú y del panel (la matriz de módulos) → mismo cálculo para ambos.
- Home por rol que muestre **solo el trabajo propio**: bandeja de pendientes ("por validar", "vencidos", "mis compromisos") + acceso directo a la única acción frecuente.
- Principio: **menos opciones visibles, mejor foco**; lo administrativo plegado salvo admin.

## 7. Accesibilidad y responsive

- **Sin `:focus-visible`** en `institucional.css`/`frameworkV1.css` → foco invisible (crítico en fondos rojos).
- **`<title>` genérico** salvo inicio y cuentas (`base.html:7`).
- **Errores no asociados**: solo `p.error`; falta `aria-invalid`/`aria-describedby` y color de borde.
- **Contraste**: textos secundarios `#8a9099` < 4.5:1.
- **Sidebar** 250 px fijo sin colapso móvil (`institucional.css:27-32`).
- **Kanban** sin `role`/`aria-live`/`aria-grabbed`.

## 8. Especificación de rediseño (principios)

- **Una tarea, una pantalla.** El home muestra el trabajo del rol; el resto queda en segundo plano.
- **Un objetivo por formulario.** Secciones (`fieldset`) con lo esencial visible y lo secundario en "avanzado".
- **Nada a mano si se puede elegir.** Fechas con calendario; selecciones con búsqueda; RUT/teléfono con teclado y máscara.
- **Feedback inmediato y suave.** Kanban animado, sin recargas; mensajes claros; errores ligados al campo.
- **La ficha muestra lo registrado; el listado, lo que decide.**

## 9. Cómo se mantiene

- Regenerar la parte funcional con `PROMPT_DETALLE_ABSTERGO.md`; esta auditoría se revisa al rediseñar cada pantalla.
- Criterios de aceptación UX por fase: calendario funcional, multiselect con búsqueda, kanban sin recarga y con permiso respetado, navegación sin enlaces muertos, AA en flujos clave.
