# Roadmap de completitud — webapp Abstergo

- Fecha: 2026-11-24.
- Objetivo: listar **qué falta detallar/construir** para que `abstergo` sea una aplicación completa (cobertura de la spec, producto/producción y entrega académica).
- Base: `documentacion/auditoria/INFORME_DETALLE_ABSTERGO.md` (auditoría) y `documentacion/auditoria/PROMPT_DETALLE_ABSTERGO.md` (regenerar).
- Estado verificado hoy: **131 pruebas** en verde, `ruff` limpio, `scripts/verificar.sh` OK, CI corriendo `verificar.sh`. `check --deploy`: **7 issues** con `PRODUCCION_SEGURA` apagado y **3** con `=1`.

**Cómo leerlo**
- Tipo: **especificar** (falta una decisión), **construir** (falta implementación), **documentar** (falta artefacto/actualización).
- Prioridad: **P1** bloquea "completa" · **P2** necesario para operar bien · **P3** limpieza/analítico.
- Cada fila tiene un criterio de "hecho" binario y verificable.

## A · Requisitos y decisiones de negocio (especificar)

| ID | Qué falta | Tipo | Estado actual (evidencia) | Criterio de hecho | Prioridad |
|---|---|---|---|---|---|
| A-01 | Cerrar `D-01..D-16` | especificar | abiertas (`SGR_Especificacion_Funcional.md` §12) | cada decisión con valor y parametrizada | P1 |
| A-02 | Política de PII: conservación/eliminación y base de licitud | especificar | modelos en `apps/cumplimiento/models.py` sin automatización | política escrita + retención implementada | P1 |
| A-03 | Lista de eventos auditables y su retención (RNF-007) | especificar | `apps/cumplimiento/auditoria.py` parcial | lista cerrada + retención documentada | P2 |
| A-04 | Límites de evidencia por ítem y nombre generado (RNF-009) | especificar | `Evidencia.EXTENSIONES`/`TAMANO_MAX` globales (`sgr/models.py:538`) | límite por ítem + nombre del sistema | P2 |
| A-05 | Umbrales y destinatarios de alertas configurables y auditados (RF-037) | especificar | umbrales fijos en `sgr/alertas.py` | configurables + auditados | P2 |
| A-06 | SLA, disponibilidad y respaldo | especificar | no documentado | doc de operación con objetivos | P2 |

## B · Casos de uso y trazabilidad (documentar)

| ID | Qué falta | Tipo | Estado actual (evidencia) | Criterio de hecho | Prioridad |
|---|---|---|---|---|---|
| B-01 | Fichas CU faltantes | documentar | CU-01..CU-10 en `entregables/CASOS DE USO DETALLADOS.docx` | CU para ajustes, ausencias, organizaciones, alertas, casos sociales e informes | P2 |
| B-02 | Tabla de equivalencia `RF-01..10 ↔ RF-001..060` | documentar | CU usan `RF-01..10`; HU usan `RF-00x` | tabla única publicada | P2 |
| B-03 | Mapa `CU → pantalla → mockup` | documentar | método en `material/Relación entre los artefactos.pdf` | matriz completa | P2 |
| B-04 | Unificar numeración CU↔HU | documentar | dos esquemas distintos | un solo esquema | P2 |

## C · Esqueleto de plataforma (construir) — según `PLAN.md` §1

| ID | Qué falta | Tipo | Estado actual (evidencia) | Criterio de hecho | Prioridad |
|---|---|---|---|---|---|
| C-01 | `check --deploy` verde en CI | construir | no está en CI; 7 issues con prod off | CI corre `check --deploy` sin ERROR | P1 |
| C-02 | Email de producción | construir | `mail.E001` (backend de consola) | SMTP configurado y verificado | P1 |
| C-03 | Config por entorno `settings/{base,dev,prod}.py` | construir | ausente (`config/settings.py` único) | perfiles con `check` | P2 |
| C-04 | Auditoría central por middleware/señal | construir | se llama desde las vistas (`vistas_base.py`) | middleware/señal central | P2 |
| C-05 | Restricciones en la base (unique/check/FK) | construir | validación en form/serializer | constraints en modelos + migración | P2 |
| C-06 | Borrado lógico consistente en Admin | construir | Admin hace `DELETE` real | Admin respeta la baja lógica | P3 |
| C-07 | Seeding idempotente y no destructivo | construir | `cargar_datos` resucita borrados | reejecutar no resucita | P3 |

## D · Módulos funcionales (construir)

| ID | Qué falta | Tipo | Estado actual (evidencia) | Criterio de hecho | Prioridad |
|---|---|---|---|---|---|
| D-01 | Ley 21.719 operativa (ARCOP, consentimiento, incidentes) | construir | `apps/cumplimiento` sin `urls.py`/`views.py`; solo Admin | vistas web o API + retención | P2 |
| D-02 | Importación real de las 2 709 organizaciones JJVV | construir/verificar | comando `importar_jjvv` existe; `PLAN.md` dice "sin importar aún" | informe de calidad reproducible | P2 |
| D-03 | Casos sociales: plazos y valores visibles (RN-017/018) | construir | constantes en `sgr/validaciones.py`; visualización por verificar | mostrados y probados | P2 |
| D-04 | Informes/reportes consolidados (RF-033) | construir | exportación `.xlsx` por listado (`vistas_base.py:58`) | informe consolidado filtrable | P3 |
| D-05 | Decidir exposición de `apps/cumplimiento` | especificar | módulo solo Admin | decisión escrita | P2 |

## E · API y móvil (construir/documentar)

| ID | Qué falta | Tipo | Estado actual (evidencia) | Criterio de hecho | Prioridad |
|---|---|---|---|---|---|
| E-01 | HTTPS efectivo en producción | construir | `PRODUCCION_SEGURA` opt-in; cert TLS pendiente en AWS | TLS activo y verificado | P1 |
| E-02 | OpenAPI versionado + colección de ejemplos | documentar | `/api/schema/` y docs (`config/urls.py`) | versión + colección | P2 |
| E-03 | Paridad de permisos web ↔ API | verificar | `BaseViewSet` usa `permisos.puede` (`api/views.py:74`) | prueba de paridad por rol | P2 |
| E-04 | Base del cliente Android | construir | no existe (`~/AndroidStudioProjects/PROYECTOPENKA`) | proyecto consume el OpenAPI | P3 |

## F · Calidad (construir)

| ID | Qué falta | Tipo | Estado actual (evidencia) | Criterio de hecho | Prioridad |
|---|---|---|---|---|---|
| F-01 | Medir cobertura y fijar umbral | construir | sin medición | `coverage` en CI con umbral | P1 |
| F-02 | Pruebas de `apps/api` y `apps/cumplimiento` | construir | 3 y 2 pruebas | cobertura de flujos | P2 |
| F-03 | Prueba de rendimiento RNF-001 | construir | sin medición de tableros | ≤ 5 s reproducible | P2 |
| F-04 | Unificar conteo de pruebas en la doc | documentar | 32/104/118/131 según el documento | 131 en todos | P3 |

## G · Seguridad (construir)

| ID | Qué falta | Tipo | Estado actual (evidencia) | Criterio de hecho | Prioridad |
|---|---|---|---|---|---|
| G-01 | `SECRET_KEY` ≥ 32 bytes | construir | `InsecureKeyLengthWarning` (clave 24 bytes) en JWT | sin warning | P1 |
| G-02 | `DEBUG=False` por defecto | construir | `check --deploy` W018; default `True` | default `False` | P1 |
| G-03 | MFA / directorio institucional (RNF-003) | construir | sin MFA | MFA opcional | P2 |
| G-04 | Segregación "quien registra no valida" para admin | construir | admin tiene `evidence`+`validation` (`common/permisos.py`) | regla aplicada | P2 |
| G-05 | Evidencias y PII servidas solo por permiso | verificar | `MEDIA_ROOT` fuera del estático (`settings.py`) | prueba de acceso denegado | P2 |
| G-06 | `pip-audit` en la verificación | construir | ausente | en CI | P3 |

## H · UI/UX y accesibilidad (construir)

| ID | Qué falta | Tipo | Estado actual (evidencia) | Criterio de hecho | Prioridad |
|---|---|---|---|---|---|
| H-01 | Confirmar tipo de input de fecha (flatpickr) | construir | **hecho 2026-11-24** (`CampoFecha`) | calendario funcional | P1 |
| H-02 | `:focus-visible` | construir | **hecho 2026-11-24** (`institucional.css`) | foco visible | P2 |
| H-03 | Errores con `aria-invalid`/`aria-describedby` | construir | **hecho 2026-11-24** (`FormularioCRUD.add_error`) | asociados al campo | P2 |
| H-04 | Contraste ≥ 4.5:1 | construir | **hecho 2026-11-24** (gris a `#5f6672`) | AA en textos secundarios | P2 |
| H-05 | Sidebar con colapso móvil | construir | **hecho 2026-11-24** (menú off-canvas ≤ 900 px) | colapsable | P2 |
| H-06 | `<title>` por pantalla | construir | **hecho 2026-11-24** (bloque en listado/formulario/consulta) | título por vista | P3 |
| H-07 | Breadcrumbs | construir | **hecho 2026-11-24** (migas en listado/formulario/consulta) | navegación con ruta | P3 |
| H-08 | Visor de evidencia en la validación | construir | **hecho 2026-11-24** (ficha muestra imagen/vínculo) | previsualización | P3 |
| H-09 | Estado de envío en botones de formulario | construir | **hecho 2026-11-24** (`formulario.js`) | spinner/disable | P3 |

## I · Operación y documentación (documentar)

| ID | Qué falta | Tipo | Estado actual (evidencia) | Criterio de hecho | Prioridad |
|---|---|---|---|---|---|
| I-01 | `PLAN.md` al día | documentar | declara "faltan lint y tests", "R9 ausente" | estados reales + bitácora | P1 |
| I-02 | `documentacion/pruebas.md` al día | documentar | dice "32 pruebas" y SGR fuera de alcance | 131 y SGR dentro | P1 |
| I-03 | Despliegue/TLS/backup/monitoreo | documentar | `despliegue_aws.md`; cert pendiente | doc de operación completo | P2 |
| I-04 | `documento_tecnico.md` y `vision.md` coherentes | documentar | desfases puntuales | sin contradicciones | P3 |
| I-05 | Artefactos CU/HU/DER/mockup alineados | documentar | DER no corresponde al modelo real | artefactos alineados | P3 |
| I-06 | README: integrantes | documentar | placeholder | completado | P3 |

## Definición de "aplicación completa" (DoD global)

- **Cobertura:** cada `RF/RNF/RN/CA` en **Cubierto** con prueba; cero **Faltante**; los **Parcial** con dueño y fecha.
- **Decisiones:** `D-01..D-16` y las reglas nuevas cerradas y reflejadas en código y doc.
- **Producto:** HTTPS efectivo, `SECRET_KEY`/`DEBUG` seguros, `check --deploy` sin ERROR, cobertura medida con umbral.
- **Accesibilidad:** flujos clave en AA (foco, contraste, errores asociados).
- **Operación:** despliegue reproducible, respaldo y monitoreo documentados.
- **Documentación:** `PLAN.md`, `pruebas.md`, `documento_tecnico.md`, `vision.md` y artefactos coherentes.

## Orden de cierre

- **P1 — bloquea "completa".** A-01/A-02; C-01/C-02; E-01; F-01; G-01/G-02; H-01; I-01/I-02.
- **P2.** A-03..A-06; B-01..B-04; C-03..C-05; D-01/D-02/D-03/D-05; E-02/E-03; F-02/F-03; G-03/G-04/G-05; H-02..H-05; I-03.
- **P3.** C-06/C-07; D-04; E-04; F-04; G-06; H-06..H-09; I-04..I-06.

## Cómo se verifica y se mantiene

- Cifras reales: `bash scripts/verificar.sh`, `pytest -q`, `ruff check .`, `python manage.py check --deploy`.
- Regenerar el análisis base: `documentacion/auditoria/PROMPT_DETALLE_ABSTERGO.md`.
- Regla: al cerrar un ítem, actualizar el estado aquí y el documento que corresponda (`PLAN.md`, `pruebas.md`, `documento_tecnico.md`).
