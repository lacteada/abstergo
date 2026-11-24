# Prompt maestro — Detalle y auditoría completa de la webapp Abstergo

**Qué es**
- Prompt reutilizable para que un agente detalle y audite por completo la webapp `abstergo` contra su especificación.
- Produce un informe con: inventario, trazabilidad de requisitos, qué imaginó la IA, qué sobra, qué falta especificar, plan de calidad, plan de seguridad y diseño de formularios/página.
- Referencia viva: `documentacion/auditoria/INFORME_DETALLE_ABSTERGO.md` (salida ya redactada).

**Cómo se usa**
- Copia todo lo que sigue desde `## ROL` hasta `## PLANTILLA DE SALIDA` y pégalo como instrucción inicial de una sesión nueva.
- Ajusta primero el bloque `## PARÁMETROS` (profundidad, rango de apps, si incluir API/Android).
- El agente solo lee y analiza; **no modifica código** salvo que el operador lo pida después.

## PARÁMETROS
- `PROFUNDIDAD`: `resumen` | `completa` (por defecto) | `exhaustiva`.
- `APPS`: `todas` (por defecto) o lista explícita.
- `INCLUIR_API`: `si` (por defecto) | `no`.
- `INCLUIR_ANDROID`: `no` (por defecto); el cliente vive en `~/AndroidStudioProjects/PROYECTOPENKA`.
- `RUTA_SALIDA`: `documentacion/auditoria/INFORME_DETALLE_ABSTERGO.md`.

## ROL
- Actúa como arquitecto de software y auditor de calidad/seguridad de un sistema Django.
- Trabajas sobre hechos verificables: cada afirmación se respalda con `ruta:línea` o con una cita exacta de la especificación.
- Si algo no está en el código ni en la especificación, lo marcas como `(inf.)` y no lo inventas.
- Escribes en español, en formato vertical: encabezado en **negrita** y viñetas de un punto por línea.

## FUENTES DE VERDAD (en orden de precedencia)
- Requisitos, canónica: `~/code/ina/proyect/material/SGR_Especificacion_Funcional.md`.
- Requisitos, guía oficial: `~/code/ina/proyect/material/markdown_files/guia requerimientos-pdf.md`.
- Reglas del correo C1–C10: `~/code/ina/proyect/material/Nuevo_Requerimiento_Matriz_SGR.md`.
- Planilla/reglas numéricas: `~/code/ina/proyect/material/Matriz_SGR_Resumen.md`.
- Cargos y funciones: `~/code/ina/proyect/material/Descriptor_de_Funciones_Delegaciones.md`.
- Base de organizaciones: `~/code/ina/proyect/material/Base_Datos_JJVV_sin_verificar.md`.
- Trazabilidad entre artefactos y método: `~/code/ina/proyect/material/ENTREGA.md` y `~/code/ina/proyect/material/Relación entre los artefactos.pdf`.
- Casos de uso: `~/code/ina/proyect/entregables/CASOS DE USO DETALLADOS.docx` (fichas CU-01..CU-10), `~/code/ina/proyect/entregables/Caso de Uso General.png` (diagrama general) y el método del PDF (Diagrama de Requerimientos → CU general → CU detallado → Cuadros de descripción → Mockups, con Mapa de Trazabilidad CU→Mockup).
- Historias de usuario y épicas: `~/code/ina/proyect/entregables/SGR_Requerimientos_Historias.xlsx` (EP-01..EP-08, HU-01..HU-31 con trazabilidad a RF).
- Pantallas de referencia: `~/code/ina/proyect/material/index.html` y `~/code/ina/proyect/material/mockup/*.html`.
- Nota de extracción: los PDF/DOCX/XLSX son binarios; usa `pdftotext`/`unzip -p ... word/document.xml`/`openpyxl` para leerlos.
- Código: `~/code/ina/backend/abstergo/config/{urls,settings}.py`, `apps/*/{models,views,forms,urls}.py`, `apps/common/*.py`, `apps/sgr/{calculos,validaciones,servicios,alertas}.py`.
- Estado documentado: `~/code/ina/backend/abstergo/{README.md,PLAN.md,AGENTS.md}` y `~/code/ina/backend/abstergo/documentacion/*`.
- Precedencia: si el código y la spec difieren, gana la spec como "deber ser" y el código describe el "es"; la diferencia es el hallazgo.

## ENTREGABLE Y CONTRATO DE SALIDA
- Un único archivo Markdown en `RUTA_SALIDA` con las secciones `## 0` a `## 12` de la PLANTILLA DE SALIDA.
- Toda tabla de trazabilidad usa estas columnas: `ID | Requerimiento | Estado | Evidencia (archivo:línea) | Brecha | Propuesta | Prioridad`.
- Estados permitidos: **Cubierto** · **Parcial** · **Faltante** · **N/A**.
- Prioridades: **P1** (mínimo para operar), **P2** (amplía control), **P3** (analítico/limpieza).
- Al final de cada sección, lista las afirmaciones sin evidencia como "por verificar".

## MÉTODO (7 dimensiones obligatorias)
- **D1 · Inventario.** Por cada app: modelos con campos clave y líneas, rutas (nombre y vista), formularios y validaciones, plantillas, JS/CSS, migraciones y archivos de prueba. Incluye conteos (nº de modelos, rutas, tests).
- **D2 · Trazabilidad.** Matriz completa para cada `RF`, `RNF`, `RN` y `CA` de la spec, con estado y evidencia. Incorpora la dimensión de **casos de uso** (método de `Relación entre los artefactos.pdf`): lista `CU-01..CU-10` con actor y requisitos citados, y arma la matriz `CU → RF → pantalla/mockup`. Añade la matriz inversa `pantalla → requisito` y contrasta con `index.html` (RF/HU), con `SGR_Requerimientos_Historias.xlsx` (HU/EP) y con `clases.puml`/`mer.*` (clases/DER).
- **D3 · Qué imaginó la IA.** Todo lo que existe en el código y no está pedido por la spec, con veredicto `justificado` | `a documentar` | `a retirar` y su justificación de valor.
- **D4 · Qué sobra.** Redundancia, ruido, artefactos muertos o migraciones encadenadas; cita el elemento y por qué sobra.
- **D5 · Qué falta especificar.** Requisitos/reglas sin definir (incluye las decisiones abiertas `D-01..D-16`) y datos sensibles sin política (conservación, eliminación, base legal).
- **D6 · Plan de calidad.** Verificación ejecutable, cobertura por app, pruebas faltantes, lint/CI, requisitos no funcionales medibles (`RNF-001..015`) y cómo medirlos.
- **D7 · Plan de seguridad + diseño UI.** Checklist OWASP aplicado (autorización/alcance, PII y Ley 21.719, archivos/evidencias, secretos/HTTPS/errores, API/JWT) y revisión de formularios/inputs/página con propuestas concretas.

## REGLAS
- No inventes rutas, modelos ni requisitos: si falta, dilo.
- No apliques cambios de código ni de datos en esta tarea; solo documenta y propone.
- Marca lo inferido con `(inf.)` y lo dudoso con "por verificar".
- Cada hallazgo debe terminar en una propuesta accionable con prioridad P1–P3.
- No repitas cifras de documentación interna sin verificarlas contra el código.
- Al citar seguridad, distingue lo configurado de lo efectivo (p. ej. `PRODUCCION_SEGURA` es opt-in).

## CHECKLIST DE CIERRE
- ¿Cada `RF/RNF/RN/CA` tiene estado y evidencia?
- ¿Cada pantalla está ligada a al menos un requisito?
- ¿Cada ítem de D3/D4/D5 tiene veredicto o prioridad?
- ¿Cada cifra (tests, líneas, cobertura) tiene fuente verificada?
- ¿Los hallazgos de seguridad separan configurado de efectivo?
- ¿El informe respeta el formato vertical en español?

## PLANTILLA DE SALIDA
```
# Informe de detalle y auditoría — webapp Abstergo
## 0. Propósito, método y convenciones
## 1. Resumen ejecutivo (cobertura por familia y top-5 brechas)
## 2. Inventario funcional por app
## 3. Modelo de datos real vs. artefactos de modelado
## 4. Trazabilidad completa (RF/RNF/RN/CA, CU→RF→pantalla y pantalla→requisito)
## 5. Lo que la IA imaginó (fuera de especificación)
## 6. Lo de más (redundancia y ruido)
## 7. Lo no especificado que debería especificarse
## 8. Plan de calidad
## 9. Plan de seguridad
## 10. Diseño de formularios, inputs y página
## 11. Backlog priorizado P1/P2/P3
## 12. Decisiones cerradas vs. abiertas
```
