# Informe de detalle y auditoría — webapp Abstergo

- Fecha: 2026-11-24.
- Código auditado: `~/code/ina/backend/abstergo` (Django 6.1.1 · Python 3.14 · MySQL · DRF + JWT).
- Especificación de referencia: `~/code/ina/proyect/material/SGR_Especificacion_Funcional.md`.
- Prompt que genera/regenera este informe: `documentacion/auditoria/PROMPT_DETALLE_ABSTERGO.md`.
- Comando de recon: `bash scripts/verificar.sh`, `pytest -q`, `ruff check .`.

## 0. Propósito, método y convenciones

**Propósito**
- Detallar por completo la webapp y contrastarla con la especificación SGR.
- Identificar qué construyó la IA fuera de especificación, qué sobra, qué falta especificar, y proponer planes de calidad, seguridad y UI.

**Método**
- Se leyó el código (`config/`, `apps/*`, `templates/`, `static/`) y la documentación interna y de artefactos.
- Casos de uso: `entregables/CASOS DE USO DETALLADOS.docx` (CU-01..CU-10) y método de relación de artefactos en `material/Relación entre los artefactos.pdf` (ver §4).
- Cada hallazgo se respalda con `archivo:línea` o con el nombre del bloque; lo inferido se marca `(inf.)`.

**Convenciones**
- Estados: **Cubierto** · **Parcial** · **Faltante** · **N/A**.
- Prioridad: **P1** mínimo para operar · **P2** amplía control · **P3** analítico/limpieza.
- Verificación ejecutada el 2026-11-24: **131 pruebas, 0 fallos**, `ruff` limpio, smoke OK. `scripts/verificar.sh` corre sobre SQLite temporal.

**Alcance de esta pasada**
- Se verificó estructura y evidencia de existencia; la verificación de comportamiento por escenario queda señalada como "por verificar".

## 1. Resumen ejecutivo

**Estado global**
- El sistema es un Django real y funcional: **12 apps** de negocio en `INSTALLED_APPS` (`config/settings.py`), más `apps/common` como utilidades (no es app), **24 viewsets** de API y **131 pruebas** en verde.
- Tras los pasos 3–8 de `ANALISIS_ABSTERGO.md`, los tres RF antes faltantes (RF-050 llamadas, RF-054 cartas, RF-055 agenda) **ya existen** (`apps/casos/models.py:76`, `apps/tubo/models.py:203`, `apps/tubo/views.py:459`).
- Cobertura estimada de la spec: **RF ~95 %**, **RNF ~75 %**, **RN ~95 %**, **CA ~95 %** (estimación por evidencia de código; "por verificar" a nivel de comportamiento).

**Top-5 brechas por impacto**
- **Documentación desalineada** (P1): `~/SYSTEM_ARCHITECTURE.md` dice que el `coordinador` está "acotado a su delegación", pero el código es `ALCANCE_GLOBAL = {ADMIN, COORDINADOR}` (`apps/common/permisos.py:47`); `documentacion/pruebas.md` aún declara las tareas trimestrales "fuera de alcance" cuando el módulo SGR está implementado.
- **Parámetros sin versionado histórico** (P1): RF-038. Cambiar una meta/ponderador puede alterar lecturas de períodos cerrados; solo hay `version` en `RegistroGestion` y `Periodo`.
- **Segregación "quien registra no valida" no aplica al admin** (P2): el admin tiene `evidence` y `validation` de escritura (`apps/common/permisos.py`), por lo que puede registrar y aprobarse a sí mismo.
- **Trazabilidad de auditoría incompleta** (P2): RNF-007. `cumplimiento/auditoria.py` cubre lecturas/altas del CRUD, pero no todos los eventos críticos; `apps/api` no audita.
- **UI accesibilidad y errores** (P2): errores por campo sin `aria-invalid`/`aria-describedby`, sin `:focus-visible`, contraste bajo en textos secundarios y posible calendario inerte (ver §10).

## 2. Inventario funcional por app

**Núcleo de cálculo — `apps/sgr/`**
- 11 modelos: `Periodo` (`models.py:105`), `Area` (`:189`), `Indicador` (`:238`), `MetaIndicador` (`:273`), `RegistroGestion` (`:329`), `AjusteConducta` (`:447`), `Ausencia` (`:495`), `Evidencia` (`:538`), `Validacion` (`:606`), `Comentario` (`:672`), `Alerta` (`:701`).
- Dominio puro: `calculos.py` (`porcentaje`, `ponderado`, `semaforo`, `meta_al_dia`, `total_ponderado`), `validaciones.py` (`evaluar_puntaje`, `excede_tope_diario`, `en_semana_actual`), `servicios.py` (tableros), `alertas.py` (`generar_alertas` idempotente).
- Rutas: `/sgr/`, `/sgr/global/`, `/sgr/personal/<pk>/` y CRUD de 11 entidades (`apps/sgr/urls.py`).

**Cuentas y acceso — `apps/cuentas/`**
- `Rol` (`models.py:15`), `Usuario` (`:69`, email como `USERNAME_FIELD`), `RecuperacionPassword` (`:182`, OTP 6 dígitos, máx 5 intentos).
- Login por correo, recuperación OTP + enlace firmado, invitación por correo, activación, grupos espejo (`grupos.py`).
- 8 migraciones; 25 pruebas en el mayor archivo de tests.

**Organización y catálogos**
- `apps/organizacion`: `Delegacion` (`:16`), `Cargo` (`:69`), `Territorio` (`:111`).
- `apps/catalogos`: `Meta` (`:18`), `TipoAtencion` (`:49`), `SubAtencion` (`:87`, con `forma`).
- `apps/ciudadanos`: `Vecino` (`:14`, RUT único normalizado módulo 11).

**Atención, casos y comunidad**
- `apps/atenciones`: `Atencion` (`:9`), flujo "Crear Atención" con búsqueda de vecino e historial (`views.py:60`).
- `apps/casos`: `CasoSocial` (`:24`, `MAX_GESTIONES=3`) y **`Llamada`** (`:76`, generada por señal en `signals.py`).
- `apps/comunidad`: `Organizacion` (`:43`) con directiva (presidente/tesorero/secretario) e importador JJVV.

**Tubo y cartas — `apps/tubo/`**
- `TareaTubo` (`:42`) con `TRANSICIONES` y `HistorialEstado` (`:173`), tablero kanban (`views.py:108`), `Mover`, `Reasignar`, `EnviarAlTubo`.
- **`Carta`** (`:203`) con kanban propio (`views.py:363`) y vista **`Agenda`** (`:459`).

**Cumplimiento y API**
- `apps/cumplimiento`: `ActividadTratamiento`, `SolicitudTitular`, `IncidenteSeguridad`, `RegistroAuditoria` (append-only), `Consentimiento`. Sin `urls.py` ni `views.py`; solo Admin y `auditoria.py`.
- `apps/api`: 24 viewsets + auth JWT; contrato **en inglés** con `source=`. `apps/api/urls.py`.

**Conteos**
- Migraciones: sgr 10, cuentas 8, organizacion 7, tubo 7, catalogos 6, casos 4, ciudadanos 4, comunidad 4, atenciones 3, cumplimiento 1; panel y api sin migraciones.
- Pruebas: **131** en verde (`pytest -q`).

## 3. Modelo de datos real vs. artefactos de modelado

**Real (Django)**
- Entidades: `Delegacion`, `Cargo`, `Territorio`, `Rol`, `Usuario`, `Meta`(catálogo de delegación), `TipoAtencion`, `SubAtencion`, `Vecino`, `Atencion`, `CasoSocial`, `Llamada`, `Organizacion`, `Periodo`, `Area`, `Indicador`, `MetaIndicador`, `RegistroGestion`, `AjusteConducta`, `Ausencia`, `Evidencia`, `Validacion`, `Comentario`, `Alerta`, `TareaTubo`, `HistorialEstado`, `Carta`.

**Artefactos de la Primera Evaluación**
- `material/mer.dbml` y `material/mer_script.sql`: 13 tablas con `Funcionario`, `Cargo_Funcion`, `Actividad`, `Compromiso`, `Compromiso_Indicador`, `Evidencia`, `Validacion`, `Auditoria`.
- `material/entregables/script2.sql`: 11 tablas, **incoherente con `mer_script.sql`** (FK de `Meta`, cascadas `ON DELETE`).
- `material/clases.puml`: clases `Usuario→Funcionario/Verificador/Administrador`, `Ponderacion`, `CatalogoItem`.

**Brecha**
- Los artefactos **no corresponden** al esquema implementado (no hay `Funcionario` ni `Cargo_Funcion`; hay `Usuario`, `Cargo.funciones`, `RegistroGestion`, `TareaTubo`) (P2).
- Tampoco son coherentes entre sí (`mer_script.sql` vs `script2.sql`) (P3).
- Propuesta: declarar los artefactos como "Primera Evaluación (histórico)" y derivar el DER vigente de `apps/*/models.py`.

## 4. Trazabilidad completa

**Convención**
- Esta sección cubre RF/RNF/RN/CA (arriba), los casos de uso CU-01..CU-10 (abajo) y las matrices inversas pantalla→requisito.
- Evidencia = `archivo:línea` o bloque. "por verificar" = existe en código, falta prueba de comportamiento.

**RF-001..007, 038 · Configuración**
| ID | Estado | Evidencia |
|---|---|---|
| RF-001 Delegaciones CRUD | Cubierto | `apps/organizacion/views.py:14-72` |
| RF-002 Usuarios con estado/cargo/delegación/roles | Cubierto | `apps/cuentas/forms.py`, `models.py:69` |
| RF-003 Cargos con funciones e ítems | Cubierto | `organizacion/models.py:69`, `sgr/models.py:238` |
| RF-004 Catálogos tipo/subatención | Cubierto | `catalogos/models.py:49,87` |
| RF-005 Períodos | Cubierto | `sgr/models.py:105` |
| RF-006 Ponderadores con sobrescritura | Cubierto | `sgr/models.py:273` (`funcionario` FK), `Area.excepcion_ponderadores` |
| RF-007 Metas/umbral/topes/semáforo | Cubierto | `sgr/models.py:105` (`umbral_*`, `tope_*`) |
| RF-038 Versionar parámetros | Parcial | solo `RegistroGestion.version`; sin histórico de metas/ponderadores |

**RF-008..015, 039..045, 050..052 · Registro y evidencias**
| ID | Estado | Evidencia |
|---|---|---|
| RF-008 Ficha personal | Cubierto | `sgr/views.py:509` |
| RF-009 Registrar actividades | Cubierto | `sgr/models.py:329` |
| RF-010 Validar campos | Cubierto | `common/validators.py` |
| RF-011 Código único | Cubierto | `common/referencia.py:18` |
| RF-012 Adjuntar/referenciar evidencia | Cubierto | `sgr/models.py:538` |
| RF-013 Validar evidencia | Cubierto | `sgr/models.py:606` |
| RF-014 Solo validación aprobada suma | Cubierto | `sgr/validaciones.py` (`evaluar_puntaje`) |
| RF-039 Tipo de solicitante | Cubierto | `sgr/models.py:329`, `validaciones.py` |
| RF-040 Nombre y teléfono | Cubierto | `validaciones.py` (`evaluar_puntaje`) |
| RF-041 7 ingresos/día | Cubierto | `validaciones.py:11,49` |
| RF-042 Cierre semanal | Cubierto | `validaciones.py:40` |
| RF-043 Preparatoria vs ejecutada | Cubierto | `sgr/models.py:329` (`etapa`) |
| RF-044 Ingresos sospechosos | Cubierto | `sgr/alertas.py:73` |
| RF-045 Ítems bajo puntaje/tope | Cubierto | `sgr/views.py:509` |
| RF-050 Llamadas preventivas | Cubierto | `casos/models.py:76`, `casos/signals.py` |
| RF-015 Caso social 3 gestiones | Cubierto | `casos/models.py:21` |
| RF-051 Campos/plazos del caso | Parcial | `validaciones.py:23-26` (constantes; "por verificar" visualización) |
| RF-052 Reingresos de informe | Parcial | `casos/models.py:24` (`reingreso`), `validaciones.py:29` |

**RF-016..021, 053..055 · Agenda y cartas**
| ID | Estado | Evidencia |
|---|---|---|
| RF-016 Compromisos | Cubierto | `tubo/models.py:42` |
| RF-017 Campos del compromiso | Cubierto | `tubo/models.py:42` (`clean`) |
| RF-018 Estados/transiciones | Cubierto | `tubo/models.py:18,28,173` |
| RF-019 Vencidos | Cubierto | `tubo/models.py:42` (`vencida`, `dias_atraso`) |
| RF-020 Cierre alimenta ítem | Parcial | `sgr/models.py:606` (`Validacion.save` cierra compromiso) |
| RF-021 Resumen colectivo | Cubierto | `tubo/views.py:108` |
| RF-053 Reasignar | Cubierto | `tubo/views.py:292` |
| RF-054 Tubo de cartas | Cubierto | `tubo/models.py:203`, `tubo/views.py:315,363` |
| RF-055 Agenda del delegado | Cubierto | `tubo/views.py:459` |

**RF-022..031, 046..049 · Ajustes, ausencias y cálculos**
| ID | Estado | Evidencia |
|---|---|---|
| RF-022 Calcular avance | Cubierto | `sgr/servicios.py:_avance` |
| RF-023 % cumplimiento | Cubierto | `sgr/calculos.py:26` |
| RF-024 Ponderado con topes | Cubierto | `sgr/calculos.py:34,72` |
| RF-025 Ajustes parametrizables | Cubierto | `sgr/models.py:447` |
| RF-046 Felicitaciones | Cubierto | `validaciones.py:15,16` |
| RF-047 Reclamos | Cubierto | `validaciones.py:19` |
| RF-048 Ausencias | Cubierto | `sgr/models.py:495` |
| RF-026 Meta al día | Cubierto | `sgr/calculos.py:67` |
| RF-027 Semáforo | Cubierto | `sgr/calculos.py:52` |
| RF-028 Tablero personal | Cubierto | `sgr/views.py:509` |
| RF-029 Tablero de delegación | Cubierto | `sgr/views.py:483` |
| RF-049 Vista de equipo | Cubierto | `sgr/servicios.py:91` |
| RF-030 Actividad reciente | Cubierto | `sgr/servicios.py:91` ("por verificar" en UI) |
| RF-031 Vista global por cargos | Cubierto | `sgr/views.py:542` |

**RF-032..037, 056..060 · Consulta y organizaciones**
| ID | Estado | Evidencia |
|---|---|---|
| RF-032 Buscar/filtrar | Cubierto | `common/vistas_base.py:146` |
| RF-033 Informes/export | Cubierto | `common/vistas_base.py:58` (openpyxl) |
| RF-034 Trabajo simultáneo | Cubierto | `sgr/models.py:329` (`version`) |
| RF-035 Comentarios | Cubierto | `sgr/models.py:672` |
| RF-036 Trazabilidad | Parcial | `cumplimiento/auditoria.py` (cobertura incompleta) |
| RF-037 Alertas | Cubierto | `sgr/alertas.py:14` |
| RF-056 Catálogo de organizaciones | Cubierto | `comunidad/models.py:43` |
| RF-057 Importar JJVV | Cubierto | comando `importar_jjvv` |
| RF-058 Cambiar estado de organización | Cubierto | `comunidad/models.py:43` (`situacion`) |
| RF-059 Vincular actividades a organización | Cubierto | `sgr/models.py:329` (`organizacion` FK) |
| RF-060 Alertar sin visita | Cubierto | `comunidad/models.py:43` (`sin_visita`), `alertas.py` |

**RNF-001..015**
| ID | Estado | Evidencia / nota |
|---|---|---|
| RNF-001 Rendimiento | Parcial | sin medición de tableros; solo smoke |
| RNF-002 Concurrencia | Cubierto | `sgr/models.py:329` (`version`) |
| RNF-003 Autenticación | Cubierto | sesión + JWT; **ver §9** (clave HMAC corta, sin MFA) |
| RNF-004 Autorización servidor | Cubierto | `common/permisos.py`, `common/vistas_base.py:52` |
| RNF-005 Cifrado en tránsito | Parcial | `settings.py` bloque `PRODUCCION_SEGURA` (opt-in); cert AWS pendiente |
| RNF-006 Integridad | Cubierto | validadores + FK `PROTECT` |
| RNF-007 Auditoría | Parcial | `cumplimiento/auditoria.py` |
| RNF-008 Privacidad | Parcial | modelos Ley 21.719; sin política de conservación/eliminación automatizada |
| RNF-009 Evidencias | Cubierto | `sgr/models.py:538` (`EXTENSIONES`, `TAMANO_MAX=5MB`); nombre no generado por el sistema |
| RNF-010 Usabilidad | Parcial | etiquetas claras; faltan accesibilidad y errores asociados (§10) |
| RNF-011 Compatibilidad | Cubierto | responsive; sidebar fija sin colapso |
| RNF-012 Configurabilidad | Cubierto | parámetros como datos |
| RNF-013 Escalabilidad | Cubierto | modelo extensible |
| RNF-014 Exportación y APIs | Cubierto | `.xlsx` + API v1 |
| RNF-015 Errores y secretos | Parcial | `403/404/500.html` existen sin diseño; `SECRET_KEY` corta |

**RN-001..022**
- Cubierto: RN-002..016, RN-021, RN-022.
- **RN-001** → Cubierto (`Area.excepcion_ponderadores`; "por verificar" que advierta la suma ≠ 100 %).
- **RN-017** (plazos del caso) → Parcial (`validaciones.py:23-26`).
- **RN-018** (valor del informe) → Parcial (`validaciones.py:29`).
- **RN-019** (soluciones al tubo) → Parcial (`validaciones.py:32`).
- **RN-020** (reclamos repetidos) → Cubierto (`servicios.py:25` + alerta).

**CA-01..021**
- Cubierto: CA-01..08, CA-10..18, CA-20, CA-21.
- **CA-09** (historial completo) → Parcial (auditoría incompleta).
- **CA-19** (reclamos repetidos) → Cubierto (RN-020).

**Casos de uso (CU-01..CU-10)**
- Fuente de las fichas: `~/code/ina/proyect/entregables/CASOS DE USO DETALLADOS.docx`; diagrama general: `~/code/ina/proyect/entregables/Caso de Uso General.png` (imagen, no legible como texto aquí).
- Método y mapa `CU → mockup` en `~/code/ina/proyect/material/Relación entre los artefactos.pdf` (Diagrama de Requerimientos → CU general → CU detallado → Cuadros de descripción → Mockups; ejemplo genérico "Gestionar Empleados").
- Las fichas son 10, con actor y requisitos citados:

| CU | Nombre | Actor principal | Requisitos citados |
| CU-01 | Registrar Actividad | Funcionario | RF-01, RN-01 (include CU-09) |
| CU-02 | Subir Evidencia | Funcionario | RF-02, RNF-04 (include CU-01) |
| CU-03 | Validar Evidencia | Verificador | RF-03, RN-03 |
| CU-04 | Gestionar Agenda Colectiva | Funcionario, Delegado | RF-04, RN-04 |
| CU-05 | Configurar Metas y Ponderaciones | Coordinador | RF-05, RN-05 |
| CU-06 | Administrar Usuarios y Roles | Administrador | RF-06, RNF-01 |
| CU-07 | Consultar Tablero Personal | Funcionario | RF-07, RN-07 |
| CU-08 | Consultar Resumen Delegación | Delegado | RF-08, RN-08 |
| CU-09 | Autenticarse | Todos los actores | RF-09, RNF-02 |
| CU-10 | Auditar Cambios | Administrador | RF-10, RNF-03 |

**Cobertura CU vs. implementación**
- CU-01 → `sgr:registros`; CU-02 → `sgr:evidencias`; CU-03 → `sgr:validaciones`; CU-04 → `tubo:tablero`/`tubo:agenda`; CU-05 → `sgr:metas`/`periodos`/`indicadores`; CU-06 → `cuentas:usuarios`/`roles`; CU-07 → `sgr:personal/<pk>`; CU-08 → `sgr:tablero`; CU-09 → `cuentas:login` + API auth; CU-10 → `cumplimiento.RegistroAuditoria`.
- Los 10 CU tienen pantalla; el más débil es **CU-10 Auditar Cambios** (auditoría parcial, §9).
- Brecha de cadena de valor: los CU cubren ingesta→compromiso→ejecución→evidencia→verificación→configuración→monitoreo, pero **no hay CU** para ajustes de conducta (RF-025/046/047), ausencias (RF-048), organizaciones comunitarias (RF-056..060), alertas (RF-037), casos sociales (RF-015) ni informes/exportación (RF-033) → **P2**.
- Brecha de numeración: las fichas CU citan `RF-01..RF-10`, mientras la matriz de HU (`SGR_Requerimientos_Historias.xlsx`) y la spec canónica usan `RF-001..RF-060`; falta la tabla de equivalencia → trazabilidad `CU → RF` no verificable → **P2**.

**Matriz inversa pantalla → requisito (resumen)**
- `/` Inicio por rol → RF-028, RF-029; selector delegación/período → RF-032.
- `/sgr/`, `/sgr/global/`, `/sgr/personal/<pk>/` → RF-022..031, RF-045, RF-049.
- `/tubo/`, `/tubo/agenda/`, `/tubo/cartas/` → RF-016..021, RF-053..055.
- `/atenciones/`, `/casos/`, `/casos/llamadas/` → RF-008..014, RF-050..052, RF-015.
- `/organizaciones/` → RF-056..060.
- `/delegaciones/`, `/cargos/`, `/territorios/`, `/usuarios/`, `/roles/`, `/metas/`, `/tipos-atencion/`, `/sub-atenciones/` → RF-001..007.

## 5. Lo que la IA imaginó (fuera de especificación)

**Cómo leerlo**
- Veredicto: **justificado** (aporta y se mantiene) · **a documentar** (sirve pero la spec no lo reconoce) · **a retirar** (sin uso o contra la spec).

**Funcionalidad añadida que la spec SGR no pide**
- API v1 REST + JWT + OpenAPI (`apps/api/`) — la spec solo pide "APIs controladas" → **justificado** (cliente Android `PROYECTOPENKA`).
- Módulo Ley 21.719 (`apps/cumplimiento/`: RAT, ARCOP, incidentes, auditoría, consentimiento) — no está en la spec SGR → **a documentar** (y decidir si se expone en web/API).
- Ciclo de cuenta: OTP + enlace firmado, invitación y activación, grupos espejo (`apps/cuentas/`) — la spec no define RF de autenticación → **justificado**.
- Delegación autorizada (M2M) + delegación activa en sesión + selector en cabecera (`common/delegaciones.py`, `panel`) → **justificado**.
- `Territorio` como entidad separada (`organizacion/models.py:111`) — la spec lo infiere → **justificado**.
- Referencia visible `PREFIJO-NN` inmutable y buscable en todas las entidades (`common/referencia.py`) → **justificado**.
- Borrado lógico triple (desactivar/eliminar/reactivar) → **a documentar** (la spec solo menciona desactivar organizaciones).
- Django Admin y comandos de operación (`cargar_datos`, `generar_vecinos`, `importar_jjvv`, `generar_alertas`) → **justificado**.
- Kanban drag&drop del tubo y de cartas + vista `Agenda` → **justificado** (RF-054/055).
- Tour `guia.js`, `mi_perfil`, `privacidad`, combobox de FK (`common/widgets.py`, `autocomplete.py`) → **a documentar** (no está en spec; mejora UX).

**Veredicto global**
- La mayoría de lo imaginado es infraestructura de calidad o trazabilidad con valor demostrable; el ítem que tensiona más el alcance es **`apps/cumplimiento`**, que conviene reconocer como módulo propio en la spec.

## 6. Lo de más (redundancia y ruido)

- Migraciones de `Carta` encadenadas en `apps/tubo/migrations/` (`0003_carta`, `0005_carta`, `0007_carta_tipo`) → **P3**, hay churn de esquema; consolidar en el estado final ya está, no requiere acción de datos.
- `Llamada` cuelga del módulo de permisos `cases` y `Carta` del módulo `tasks` (`common/permisos.py:223`) → **P3**, no tienen módulo propio; si RR.HH. exige permisos distintos, crear módulos.
- `Agenda` es una vista derivada de `TareaTubo`, no una tabla → **N/A** (diseño válido, solo dejarlo explícito).
- Documentación con conteos de pruebas inconsistentes entre `PLAN.md`, `pruebas.md`, `resumen_codigo.md` y esta auditoría → **P3**, unificar a la cifra verificada (131).
- Numeración de RF distinta entre artefactos: las fichas CU usan `RF-01..RF-10`, las HU y la spec usan `RF-001..RF-060` (`entregables/CASOS DE USO DETALLADOS.docx` vs `entregables/SGR_Requerimientos_Historias.xlsx`) → **P2**, falta tabla de equivalencia.

## 7. Lo no especificado que debería especificarse

**Decisiones abiertas heredadas de la spec (`D-01..D-16`)**
- D-01 topes (120 % ítem / 150 % total): confirmar si ambos rigen.
- D-02 meta al día: días corridos vs hábiles y tope 100 %.
- D-03 valor del reclamo por cargo (−0,20/−0,30).
- D-04 excepción de suma de ponderadores (Planificación y Gestión = 85 %).
- D-05 ítem "Emergencia": meta = avance acreditado completo.
- D-06 límite de 7/día: por fecha de ingreso y rechazo del exceso.
- D-07 cargos sin hoja de metas: construir solo los medibles.
- D-08 período vigente y creación del 4.º trimestre.
- D-09/D-10 valores de informe y fórmula de "soluciones al tubo".
- D-11 evidencia obligatoria solo en ítems marcados.
- D-12 quién es el verificador y su designación.
- D-13 RUT obligatorio solo en caso social.
- D-14 resumen vs semáforo: una sola fuente de cálculo.
- D-15 mínimo 80 %: efecto solo informativo.
- D-16 clasificación de organizaciones (tipo/subtipo) manual o asistida.

**Reglas nuevas que faltan (P1/P2)**
- Política de conservación y eliminación de datos personales (RUT, teléfono, nombre) y base de licitud por tratamiento (RNF-008).
- Definición de eventos auditables completos y su retención (RNF-007).
- Límites de evidencia aceptados por ítem y política de nombre de archivo generado por el sistema (RNF-009).
- Umbrales y destinatarios de alertas auditados (RF-037).
- Acuerdo de nivel de servicio (RNF-001) y respaldo/disponibilidad (fuera de código, documentar).
- MFA y directorio institucional para RNF-003.

## 8. Plan de calidad

**Estado actual verificable**
- `bash scripts/verificar.sh` → `check`, migraciones sin cambios, `migrate`, `cargar_datos`, `ruff`, `pytest`, smoke de rutas y API: **OK**.
- `pytest -q` → **131 passed**; `ruff check .` → **All checks passed**.

**Brechas de prueba**
- `apps/api` (3 pruebas) y `apps/cumplimiento` (2 pruebas) tienen cobertura muy baja frente a sus líneas → **P2**.
- RNF-001 sin medición: no hay prueba de tiempo para tableros consolidados (objetivo ≤ 5 s) → **P2**.

**Propuestas**
- Medir cobertura real (p. ej. `coverage.py`) y fijar umbral por app; publicar el número verificado, no estimado.
- Añadir pruebas de escenario para CA-09 (historial) y para los parciales RF-020/030/038/051/052 y RN-017/018/019.
- Añadir una prueba de rendimiento reproducible de `/sgr/` y `/sgr/global/` (RNF-001).
- Revisar CI en `.github/` para que exija `verificar.sh` verde.
- Unificar la cifra de pruebas en toda la documentación.

## 9. Plan de seguridad

**Configurado (verificado en `settings.py`)**
- Seguridad en producción opt-in con `PRODUCCION_SEGURA=1`: `SECURE_SSL_REDIRECT`, cookies `Secure`, HSTS (1 año, subdominios, preload), `SECURE_CONTENT_TYPE_NOSNIFF`.
- Rate limit de login por IP (`common/ratelimit.py`, `LOGIN_INTENTOS_MAX=20`/60 s), activo solo sin `DEBUG`.
- Contraseñas con validadores Django + validador institucional (mayúscula/minúscula/especial).
- JWT access 60 min, refresh 7 días, rotación + blacklist; autorización por rol en `common/permisos.py`.
- Evidencias fuera del estático (`MEDIA_ROOT`), servidas por permiso.
- Páginas `403/404/500` propias (sin trazas).

**Riesgos y hallazgos**
- **Clave HMAC corta**: `pytest` emite `InsecureKeyLengthWarning` (clave de 24 bytes < 32) usada por SimpleJWT → **P1**: `SECRET_KEY` ≥ 32 bytes aleatorios.
- **`DEBUG` por defecto `True`** (`env_bool("DEBUG", True)`) → **P1**: el default debería ser `False`; un `.env` ausente no debe exponer trazas.
- **HTTPS efectivo depende del proxy**: `PRODUCCION_SEGURA` apagado por defecto; el certificado TLS en AWS está pendiente (documentado) → **P1** operacional.
- **Sin MFA** y con sesiones de larga vida → **P2** (RNF-003 recomendado).
- **Admin puede registrar y validar** (`evidence`/`validation` de escritura) → **P2** segregación de funciones.
- **PII**: RUT/nombre/teléfono sin política de conservación ni minimización en formularios/exportes (RF-033 exporta `.xlsx`) → **P2** (Ley 21.719).
- **Auditoría parcial**: sin cobertura en API ni en todos los eventos críticos → **P2**.
- **`CSRF_TRUSTED_ORIGINS`** y `SECURE_PROXY_SSL_HEADER` dependen del `.env`; verificar en producción que no queden host de ejemplo → **P2**.
- **Dependencias** fijadas en `requirements.txt`; sin verificación de vulnerabilidades (p. ej. `pip-audit`) → **P3**.

**Propuestas P1**
- Generar `SECRET_KEY` de 32+ bytes, `DEBUG=False` por defecto y verificarlo en el despliegue.
- Terminar TLS y activar `PRODUCCION_SEGURA=1` (paso de `sudo` en AWS, entregado como texto).
- Añadir `pip-audit` (o equivalente) a la verificación.

## 10. Diseño de formularios, inputs y página

**Base visual (verificado)**
- Dos hojas propias (`static/css/frameworkV1.css`, `institucional.css`) más SweetAlert2 y flatpickr vendorizados; iconos SVG inline; sin Bootstrap.
- Patrón único de formulario CRUD (`templates/partials/formulario.html`) con página completa y modal `<dialog>` (`static/js/modal.js`), degradación sin JS.
- Autocompletado de FK en combobox (`common/widgets.py`, `static/js/autocomplete.js`) — **buen patrón**, mantener.

**Hallazgos de input/formulario**
- **Posible calendario inerte (P1, verificar en navegador)**: `static/js/fechas.js` engancha flatpickr a `input[type="date"]`/`[type="datetime-local"]`, pero `DateField`/`DateTimeField` usan widgets por defecto de Django que renderizan `type="text"` (no hay override de widget en el proyecto). Si se confirma, los campos de fecha quedan como texto sin calendario → definir widget propio con `type="date"` o enganchar flatpickr por clase.
- **Errores no asociados al campo (P2)**: el mensaje aparece en `p.error` bajo el label, pero el input no recibe `is-invalid`/`aria-invalid`/`aria-describedby` ni color de borde.
- **Sin estado de envío (P2)**: los botones de formulario no se deshabilitan ni muestran spinner (solo el kanban).
- **Teléfono/RUT**: validados en servidor (`common/validators.py`), sin máscara ni `inputmode` de teclado en los campos de entrada.
- **Evidencia**: sin visor de imagen dedicado en la validación (el mockup sí lo tenía) → considerar previsualización en la ficha de validación.

**Hallazgos de página/layout**
- **Sin `:focus-visible` (P1 accesibilidad)**: ni `institucional.css` ni `frameworkV1.css` definen estilos de foco.
- **Contraste bajo (P2)**: textos secundarios en `#8a9099` sobre blanco/gris (~3:1) < 4.5:1 AA.
- **Listados sin `<title>` propio (P3)**: la mayoría de pantallas hereda "Sistema Municipal".
- **Sidebar fija de 250px sin colapso (P2)**: sin breakpoint móvil; en pantallas pequeñas el contenido queda comprimido.
- **Sin breadcrumbs (P3)**: el mockup los tenía; ayudan a la orientación.
- **Nav sin `aria-current="page"` (P3)**: el ítem activo solo cambia de clase CSS.
- **Campos de fecha del mockup** (`input type=date`) difieren del render real: alinear.
- **Login sin campo Delegación (N/A)**: el mockup lo tenía; el diseño real elige delegación tras entrar (decisión válida, dejar explícita).

**Propuestas concretas (P1)**
- Definir en `static/css/institucional.css` un `:focus-visible { outline: 2px solid var(--muni-base); outline-offset: 2px }`.
- Confirmar el tipo de input de fecha y, si es `text`, crear un widget compartido en `common/widgets.py` que emita `type="date"`.
- En `templates/partials/formulario.html`, añadir `aria-invalid` y `aria-describedby` al campo cuando `campo.errors`.

## 11. Backlog priorizado

**P1**
- Documentación: corregir `SYSTEM_ARCHITECTURE.md` (rol coordinador) y `documentacion/pruebas.md` (SGR dentro de alcance) — hecho parcialmente en esta pasada (ver doc).
- Seguridad: `SECRET_KEY` ≥ 32 bytes y `DEBUG` por defecto `False`.
- Inputs: confirmar/fijar el tipo de input de fecha; añadir `:focus-visible`.
- Definir política de conservación/eliminación de PII.

**P2**
- Versionado histórico de parámetros (RF-038).
- Auditoría completa de eventos críticos (RNF-007) y en API.
- Segregación "quien registra no valida" para admin.
- Accesibilidad: `aria-invalid`/`aria-describedby`, contraste, colapso de sidebar.
- Pruebas para `apps/api`, `apps/cumplimiento` y rendimiento de tableros (RNF-001).
- Completar la trazabilidad de casos de uso: fichas CU para ajustes, ausencias, organizaciones, alertas, casos sociales e informes, y unificar la numeración de RF entre CU y HU (tabla de equivalencia).
- Cerrar `D-01..D-16`.

**P3**
- Limpieza: consolidar conteos de pruebas, marcar artefactos de Primera Evaluación como históricos.
- Diseño: breadcrumbs, `<title>` por pantalla, `aria-current`, visor de evidencia.
- `pip-audit` en la verificación.

## 12. Decisiones cerradas vs. abiertas

**Cerradas**
- Aplicación de los pasos 2–8 de `ANALISIS_ABSTERGO.md`: panel por rol, `ALCANCE_GLOBAL={ADMIN, COORDINADOR}`, RF-050/054/055 implementados, RN-017/018/019 parametrizados, HTTPS/rate limit/páginas de error.

**Abiertas**
- Todas las `D-01..D-16` de la especificación §12, más política de PII, MFA y SLA.
- Exposición (o no) del módulo `apps/cumplimiento` en web/API.

**Mantenimiento de este informe**
- Regenerar con `PROMPT_DETALLE_ABSTERGO.md`; contrastar evidencia con `config/urls.py`, `apps/*/urls.py`, `apps/common/permisos.py` y `apps/sgr/*`.
- Verificación de referencia: `bash scripts/verificar.sh`.
