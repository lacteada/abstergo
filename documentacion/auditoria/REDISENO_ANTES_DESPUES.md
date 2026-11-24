# Rediseño antes/después por formulario — Abstergo

- Fecha: 2026-11-24.
- Regla: cada formulario trae su **ANTES** (estado actual verificado) y un espacio **DESPUÉS** en blanco.
- **Nada se implementa hasta que tú escribas el DESPUÉS** de ese formulario; los cambios de modelo/migración requieren tu aprobación explícita aquí.
- Cómo llenarlo: edita el bloque `DESPUÉS` (campos, agrupación, obligatoriedad, si toca el modelo) y avísame; implemento ese formulario y paso al siguiente.

**Leyenda de widgets (ANTES)**
- `text` = `TextInput`; `fecha(text)` = `DateField` sin `type=date`; `select` = `ModelChoiceField` sin búsqueda; `select-busca` = con autocompletado; `multi` = `SelectMultiple` sin búsqueda; `number`, `check`, `file`, `textarea`.

**Transversal (Fase A) — aplicado a todos, sin tocar modelos**
- Estado: **cerrado** 2026-11-24 (131 pruebas OK, ruff limpio).
- **Fechas con calendario**: todo `DateField`/`DateTimeField` sale como `type=date`/`datetime-local` (`CampoFecha`/`CampoFechaHora` en `common/widgets.py`), con formato ISO; `flatpickr` (ya enganchado a esos tipos) entrega el calendario en español.
- **Agrupación en filas**: `FormularioCRUD.filas` + `distribucion` agrupan campos; los 22 formularios quedaron con filas.
- **Selects y multiselect con búsqueda**: los FK registrados usan combobox; el M2M (`Usuario.delegaciones_autorizadas`) usa `SelectMultipleBuscable` + `multibuscable.js` (etiquetas con búsqueda). Se registró `Rol` en el motor.
- **RUT/teléfono**: teléfono con `inputmode="tel"` (`CampoTelefono`); RUT con `placeholder`, `maxlength` y `autocapitalize`.
- **Accesibilidad**: `:focus-visible` global; errores con `aria-invalid`/`aria-describedby`; `<title>` por pantalla; contraste de textos secundarios a `#5f6672`; menú off-canvas con botón en pantallas ≤ 900 px.

---

## A. Cuentas

### A1 · `UsuarioForm` (`apps/cuentas/forms.py:33`)
- ANTES: `nombre`(text,req) · `apellido`(text) · `email`(email,req al crear) · `rol`(**select**, no buscable) · `cargo`(select-busca) · `delegacion`(select-busca, acotada) · `delegaciones_autorizadas`(**multi**, sin búsqueda) · `is_active`(check; se quita al crear).
- Problemas: multiselect sin búsqueda; `rol` en select plano.
- ¿Toca el modelo? no (presentación).
- DESPUÉS: ____

### A2 · `RolForm` (`apps/cuentas/forms.py:26`)
- ANTES: `nombre`(text,req) · `descripcion`(text).
- DESPUÉS: ____

## B. Organización

### B1 · `DelegacionForm` (`apps/organizacion/forms.py:5`)
- ANTES: `nombre`(text,req) · `direccion`(text) · `comuna`(text) · `responsable`(select-busca) · `estado`(select).
- DESPUÉS: ____

### B2 · `CargoForm` (`apps/organizacion/forms.py:12`)
- ANTES: `nombre`(text,req) · `descripcion`(text) · `funciones`(textarea).
- DESPUÉS: ____

### B3 · `TerritorioForm` (`apps/organizacion/forms.py:19`)
- ANTES: `nombre`(text,req) · `delegacion`(select-busca,req; **no acotada**) · `estado`(select).
- DESPUÉS: ____

## C. Catálogos

### C1 · `MetaForm` (`apps/catalogos/forms.py:8`)
- ANTES: `nombre`(text,req) · `descripcion`(text) · `delegacion`(select-busca,req,acotada) · `estado`(select).
- DESPUÉS: ____

### C2 · `TipoAtencionForm` (`apps/catalogos/forms.py:16`)
- ANTES: `nombre`(text,req) · `descripcion`(text) · `estado`(select).
- DESPUÉS: ____

### C3 · `SubAtencionForm` (`apps/catalogos/forms.py:22`)
- ANTES: `nombre`(text,req) · `tipo_atencion`(select-busca,req) · `forma`(select) · `estado`(select).
- DESPUÉS: ____

## D. Ciudadanos

### D1 · `VecinoForm` (`apps/ciudadanos/forms.py:6`)
- ANTES: `nombre`(text,req) · `rut`(text,req, sin `inputmode`/máscara) · `direccion`(text) · `telefono`(text, sin `inputmode=tel`) · `territorio`(select-busca,req) · `tipo_gestion`(text) · `estado`(select).
- ¿Toca el modelo? decidir si el teléfono/RUT cambian de tipo/campos.
- DESPUÉS: ____

## E. Atenciones y casos

### E1 · `AtencionForm` (`apps/atenciones/forms.py:25`)
- ANTES: `tipo_atencion`(select-busca,req) · `sub_atencion`(**select dependiente**, no buscable) · `motivo`(text,req) · `detalle`(textarea) · `estado`(select,req) · `canal`(select).
- Flujo: se alcanza solo tras buscar un vecino (`partials/crear_atencion.html`).
- DESPUÉS: ____

### E2 · `CasoSocialForm` (`apps/casos/forms.py:5`)
- ANTES: `vecino`(select-busca,req) · `responsable`(select-busca) · `fecha_apertura`(fecha(text),req) · `motivo`(text,req) · `estado`(select,req) · `reingreso`(check) · `caso_anterior`(**select**, no buscable) · `observaciones`(textarea).
- DESPUÉS: ____

### E3 · `LlamadaForm` (`apps/casos/forms.py:20`)
- ANTES: `vecino`(select-busca,req) · `atencion`(**select**) · `motivo`(text) · `fecha_programada`(fecha(text)) · `estado`(select,req).
- DESPUÉS: ____

## F. Comunidad (organizaciones) — foco directiva

### F1 · `OrganizacionForm` (`apps/comunidad/forms.py:13`)
- ANTES (16 + 6 dinámicos = 22): `nombre`(text,req) · `domicilio_legal`(text) · `territorio`(select-busca) · `tipo`(select) · `subtipo`(select) · `situacion`(select,req) · `verificacion`(select,req) · `socios_activos`(number) · `fecha_constitucion`(fecha(text)) · `registro_pj`(text) · `fecha_inscripcion`(fecha(text)) · `registro_dir`(text) · `presidente`/`tesorero`/`secretario`(select-busca a `Vecino`) · `estado`(select,req) · `nuevo_{presidente,tesorero,secretario}_nombre`(text) · `nuevo_{...}_rut`(text).
- Hoy: la directiva ya es FK a `Vecino` (con RUT). Para crear un directivo se piden nombre+RUT, pero **si el RUT ya existe falla** (`ciudadanos/servicios.py:48-49`), es decir no reutiliza a la persona.
- Tú pediste: cada directivo con su RUT y como objeto.
- ¿Toca el modelo? no (se reusa el `Vecino` existente).
- DESPUÉS (aprobado 2026-11-24, implementado):
  - Los 3 cargos son 3 botones «+» en una fila horizontal (una sola `.campo-fila`).
  - Cada «+» abre un buscador por nombre o RUT (`/autocompletar/vecino/`); al elegir, asigna la persona.
  - Si no existe, el modal ofrece «Crear persona» (nombre + RUT); el alta se guarda **junto con la organización**, no al instante.
  - El RUT se sigue validando con dígito verificador módulo 11.
  - Se agruparon en filas: `domicilio_legal|territorio`, `tipo|subtipo`, `situacion|verificacion`, `socios_activos|registro_pj`, `fecha_constitucion|fecha_inscripcion`, y la fila de Directiva.
  - Archivos: `apps/common/widgets.py` (`SelectorPersona`), `apps/common/forms.py` (`distribucion`), `templates/partials/formulario.html`, `static/js/personas.js`, `static/css/institucional.css`, `apps/comunidad/forms.py`.
- Estado: **cerrado** (131 pruebas OK, ruff limpio).

## G. Tubo (compromisos y cartas)

### G1 · `TareaTuboForm` (`apps/tubo/forms.py:5`)
- ANTES: `titulo`(text,req) · `descripcion`(textarea) · `estado`(select,req) · `delegacion`(select-busca,req) · `territorio`(select-busca) · `tipo`(select,req) · `solicitante`(text) · `responsable`(select-busca) · `apoyo`(select-busca) · `vecino`(select-busca) · `atencion`(**select**) · `avance`(number,req) · `fecha_compromiso`(fecha(text)) · `orden`(number,req).
- DESPUÉS: ____

### G2 · `CartaForm` (`apps/tubo/forms.py:28`)
- ANTES: `asunto`(text,req) · `tipo`(select,req) · `correlativo`(number) · `destinatario`(select,req) · `remitente`(text) · `contacto`(text) · `fecha`(fecha(text),req) · `encargado`(select-busca) · `delegacion`(select-busca,req) · `estado`(select,req) · `observacion`(textarea).
- DESPUÉS: ____

## H. SGR

### H1 · `PeriodoForm` (`apps/sgr/forms.py:22`)
- ANTES: `nombre`(text,req) · `inicio`(fecha(text),req) · `termino`(fecha(text),req) · `dias`(number) · `situacion`(select,req) · `umbral_minimo`/`umbral_ambar`/`tope_item`/`tope_total`(number,req) · `estado`(select,req).
- DESPUÉS: ____

### H2 · `AreaForm` (`apps/sgr/forms.py:39`)
- ANTES: `nombre`(text,req) · `grupo`(select,req) · `cargo`(select-busca) · `responsable`(select-busca) · `delegacion`(select-busca) · `estado`(select,req).
- DESPUÉS: ____

### H3 · `IndicadorForm` (`apps/sgr/forms.py:47`)
- ANTES: `nombre`(text,req) · `grupo`(select,req) · `unidad`(select,req) · `cargo`(select-busca) · `tipo_calculo`(select,req) · `requiere_evidencia`(check) · `estado`(select,req).
- DESPUÉS: ____

### H4 · `MetaIndicadorForm` (`apps/sgr/forms.py:61`)
- ANTES: `periodo`(select-busca,req) · `area`(select-busca,req) · `indicador`(select-busca,req) · `ponderador`(number,req) · `meta`(number,req) · `funcionario`(select-busca) · `vigente_desde`(fecha(text)).
- DESPUÉS: ____

### H5 · `RegistroGestionForm` (`apps/sgr/forms.py:75`) — el más usado por el funcionario
- ANTES (20): `fecha`(fecha(text),req, hoy) · `area`(select-busca,req) · `indicador`(select-busca,req) · `vecino`(select-busca) · `funcionario`(select-busca,req) · `cantidad`(number,req) · `detalle`(textarea) · `etapa`(select,req) · `tipo_solicitante`(select,req) · `contacto_nombre`(text) · `contacto_telefono`(text, sin `inputmode`) · `accion`(text) · `actividad`(select) · `organizacion`(select-busca) · `compromiso`(select-busca) · `estado`(select,req) · `evidencia_archivo`(file) · `evidencia_vinculo`(url) · `evidencia_tipo`(text) · `version`(hidden).
- DESPUÉS: ____

### H6 · `AjusteConductaForm` (`apps/sgr/forms.py:159`)
- ANTES: `area`(select-busca,req) · `tipo`(select,req) · `fecha`(fecha(text),req) · `respaldo`(text) · `medio`(select) · `valor`(number) · `periodo`(select-busca).
- DESPUÉS: ____

### H7 · `AusenciaForm` (`apps/sgr/forms.py:165`)
- ANTES: `area`(select-busca,req) · `periodo`(select-busca) · `tipo`(select,req) · `desde`(fecha(text),req) · `hasta`(fecha(text),req) · `registrada_por`(select-busca).
- DESPUÉS: ____

### H8 · `EvidenciaForm` (`apps/sgr/forms.py:171`)
- ANTES: `registro`(**select**, req) · `archivo`(file, **req** aunque el modelo admita solo vínculo) · `vinculo`(url) · `tipo`(text).
- ¿Toca el modelo? decidir si `archivo` deja de ser obligatorio.
- DESPUÉS: ____

### H9 · `ValidacionForm` (`apps/sgr/forms.py:177`)
- ANTES: `evidencia`(**select**,req) · `decision`(select,req) · `observacion`(textarea).
- DESPUÉS: ____

### H10 · `ComentarioForm` (`apps/sgr/forms.py:183`)
- ANTES: `registro`(**select**,req) · `texto`(textarea,req).
- DESPUÉS: ____

### H11 · `AlertaForm` (`apps/sgr/forms.py:189`)
- ANTES: `tipo`(select,req) · `severidad`(select,req) · `mensaje`(text,req) · `area`(select-busca) · `resuelta`(check).
- DESPUÉS: ____

---

## Orden sugerido para llenar los DESPUÉS
1. `OrganizacionForm` (directiva/RUT — toca modelo).
2. `RegistroGestionForm` (el más usado).
3. `AtencionForm` + flujo "Crear atención".
4. `TareaTuboForm` / `CartaForm` (junto con el kanban).
5. `CasoSocialForm` / `LlamadaForm`.
6. `VecinoForm`, `PeriodoForm`/`MetaIndicadorForm`, `UsuarioForm`.
7. Resto (organización, catálogos, SGR auxiliares).

## Cómo se implementa un DESPUÉS aprobado
- Se cambia solo lo aprobado; si toca el modelo, se agrega la migración y se actualiza `documento_tecnico.md`.
- Verificación: `bash scripts/verificar.sh`, `pytest -q`, `ruff check .`.
- Se marca el formulario como **cerrado** aquí.
