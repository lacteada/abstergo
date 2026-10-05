# Sistema Municipal de Atención Ciudadana — Visión y Especificación

Documento rector del proyecto `abstergo`. Reemplaza a cualquier referencia de
planificación anterior: el proyecto se documenta como una unidad independiente.

- Fecha: 5 de octubre de 2026.
- Base de código: `/home/lct/code/ina/backend/abstergo` (Django + MariaDB).
- Estado: modelo v1 en producción de desarrollo (7 tablas). Este documento
  define el modelo v2 y las reglas transversales.

---

## 1. Qué es

Un sistema para que una municipalidad registre la atención a vecinos, administre
sus delegaciones y mantenga la información personal bajo la Ley 21.719.

- El proyecto se construye sobre la base ya existente, no en un repositorio nuevo.
- El interés está en el modelo de datos: modular, fácil de extender, con
  orientación a objetos y la mínima complejidad que cumpla.
- No se reutiliza ni se referencia el trabajo de evaluaciones previas.

---

## 2. Alcance

**Dentro**

- Rework de los mantenedores: validación por expresión regular, confirmación y
  mensajes con SweetAlert, paginación y exportación a Excel.
- Modelo de datos v2: nueva tabla de atención, responsable en la delegación y
  las tablas que exige la Ley 21.719.
- Rol Funcionario: flujo "Crear Atención" con búsqueda de vecino e historial.
- Dashboard personalizado por rol, con estadísticas y accesos según el rol.
- Adecuación a la Ley 21.719 (Ley de Protección de Datos Personales).

**Fuera (por ahora)**

- Cumplimiento de tareas y metas trimestrales del funcionario.
- Módulo Reportes y API REST.

---

## 3. Roles y permisos

Los roles se mantienen. `Rol` suma un `codigo` único y estable, para que el código
identifique el rol sin depender del nombre, que es editable.

- `admin` de Django sigue siendo el administrador del sistema, aparte del front.
- El rol Funcionario habilita el flujo "Crear Atención" y el historial de vecinos.
- El resto de roles solo ve los módulos que le correspondan en el dashboard.
- El código ramifica por `rol.codigo`, nunca por `rol.nombre`.

---

## 4. Modelo de datos v2

Principios de diseño.

- Una tabla por concepto; sin campos que mezclen responsabilidades.
- Llaves foráneas en `PROTECT` o `SET_NULL`, nunca en cascada.
- Borrado lógico en toda tabla de negocio (`eliminado`), salvo donde se indique.
- Cada tabla nueva que sea catálogo hereda de `BorradoLogico` en `apps/common`.

### 4.1 Tablas existentes (se conservan)

- `Rol`: nombre único, descripción.
- `Usuario`: correo como identificador, rol y delegación, activo/inactivo.
- `Delegacion`: código único, nombre, dirección, comuna.
- `Meta`: nombre, descripción, delegación.
- `TipoAtencion`: nombre, descripción.
- `SubAtencion`: nombre, tipo de atención.
- `Vecino`: nombre, RUT único, dirección, teléfono, territorio, tipo de gestión,
  estado.

### 4.2 Cambios a tablas existentes

- `Delegacion` suma `responsable`: FK a `Usuario`, `PROTECT`, un solo delegado.
- `Rol` suma `codigo`: único y estable, para ramificar por rol sin depender del nombre.
- En el formulario de delegación se pide nombre y responsable.
- `Delegacion.responsable` se rotula "Delegado(a)" en la interfaz, para no
  confundirlo con el Delegado de Protección de Datos de la ley.

### 4.3 Tablas nuevas — operación

**Atencion**

- `vecino`: FK a `Vecino`, `PROTECT`.
- `tipo_atencion`: FK a `TipoAtencion`, `PROTECT`.
- `sub_atencion`: FK a `SubAtencion`, `PROTECT`, opcional.
- `delegacion`: FK a `Delegacion`, `PROTECT`.
- `funcionario`: FK a `Usuario`, `PROTECT`.
- `fecha`: fecha y hora de la atención.
- `motivo`: texto breve.
- `detalle`: texto libre.
- `estado`: ingresada, en proceso, cerrada, derivada.
- `canal`: presencial, teléfono, web, opcional.

El historial de un vecino es una consulta, no una tabla aparte: se piden las
`Atencion` de ese `Vecino` y se muestran ordenadas por fecha.

### 4.4 Tablas nuevas — Ley 21.719

**ActividadTratamiento** (registro de actividades, RAT)

- `nombre`, `finalidad`, `base_licitud`, `categorias_datos`.
- `destinatarios`, `plazo_conservacion_dias`, `medidas_seguridad`.
- `responsable`: FK a `Usuario`.

**SolicitudTitular** (derechos ARCOP + bloqueo)

- `vecino`: FK a `Vecino`, `PROTECT`.
- `tipo`: acceso, rectificación, supresión, oposición, portabilidad, bloqueo.
- `fecha_solicitud`, `fecha_limite` (solicitud + 30 días corridos).
- `estado`, `fecha_respuesta`, `detalle`, `respondido_por` FK a `Usuario`.

**IncidenteSeguridad** (vulneraciones)

- `fecha_deteccion`, `descripcion`, `datos_afectados`, `gravedad`.
- `notificado_apdp` y `fecha_notificacion_apdp`.
- `notificado_titulares`.

**RegistroAuditoria** (accountability y acceso)

- `usuario`, `accion`, `tabla`, `objeto_id`, `fecha`, `ip`, `detalle`.
- Registra siempre las escrituras (crear, editar, eliminar).
- Registra además los accesos y exportaciones que expongan `Vecino` o `Atencion`,
  que son datos personales.

**Consentimiento** (solo si un tratamiento se funda en consentimiento)

- `vecino`, `actividad`, `otorgado`, `fecha`, `version_politica`, `revocado`.

### 4.5 Relaciones nuevas

- `Delegacion` 1 —— N `Atencion`.
- `Vecino` 1 —— N `Atencion`.
- `Usuario` 1 —— N `Atencion` (funcionario).
- `Usuario` 1 —— N `Delegacion` (responsable).
- `Vecino` 1 —— N `SolicitudTitular`.
- `Usuario` 1 —— N `RegistroAuditoria`.

---

## 5. Cumplimiento Ley 21.719

### 5.1 Contexto

- Ley 21.719, publicada el 13-dic-2024, vigencia plena el 1-dic-2026.
- Aplica a los órganos públicos, incluidas las municipalidades.
- Para un órgano público la base de licitud habitual es el cumplimiento de un
  deber legal o el ejercicio de funciones, no el consentimiento. El
  consentimiento se guarda solo cuando corresponde.
- La situación socioeconómica y los datos de salud son sensibles: el `motivo` y
  el `detalle` de una atención pueden contenerlos.

### 5.2 Mapeo obligación — implementación

- Registro de actividades: tabla `ActividadTratamiento`.
- Base de licitud por tratamiento: campo `base_licitud` en `ActividadTratamiento`.
- Derechos ARCOP + bloqueo: tabla `SolicitudTitular`, con plazo de 30 días.
- Seguridad y brechas: tabla `IncidenteSeguridad` y medidas técnicas.
- Accountability: tabla `RegistroAuditoria`.
- Informar al titular: política de privacidad enlazada en el login y en el sitio.
- Minimización: `Vecino` conserva solo los campos necesarios.
- Plazo de conservación: `plazo_conservacion_dias` por actividad.

### 5.3 Mínimo viable y opcional

Mínimo para poder sostener cumplimiento.

- `SolicitudTitular`, `RegistroAuditoria`, `IncidenteSeguridad`.
- `ActividadTratamiento` con base de licitud y plazo de conservación.
- Política de privacidad publicada y enlazada.
- Acceso al sistema por rol y sobre HTTPS.

Opcional, según se decida.

- `Consentimiento`, si algún tratamiento se funda en él.
- Bloqueo temporal como estado de la solicitud.
- Notificación automática de brechas.

---

## 6. Reglas de negocio transversales

Todas las reglas viven una sola vez en `apps/common` y las heredan los siete
mantenedores y los módulos nuevos.

### 6.1 Validación por expresión regular

Cada campo de entrada se valida en el formulario y, cuando aplica, en el modelo.

```text
RUT            ^\d{7,8}-[\dkK]$          + validación dígito verificador (módulo 11)
Nombre         ^[A-Za-zÁÉÍÓÚÑáéíóúñÜü' -]{2,60}$
Email          ^[^@\s]+@[^@\s]+\.[A-Za-z]{2,}$
Teléfono       ^\+?56?9?\d{8,9}$
Dirección      ^[A-Za-z0-9ÁÉÍÓÚÑáéíóúñ°#.,\- ]{5,200}$
Comuna         ^[A-Za-zÁÉÍÓÚÑáéíóúñ' ]{3,80}$
Código         ^[A-Z0-9\-]{2,40}$
Catálogo       ^.{2,120}$
OTP            ^\d{6}$
```

- El RUT se normaliza (sin puntos, con guion) antes de validar y de buscar.
- El dígito verificador se calcula por módulo 11; un RUT con DV inválido se rechaza.

### 6.2 SweetAlert

- Confirmación antes de eliminar cualquier registro.
- Aviso de éxito o de error tras crear, editar o eliminar.
- Los errores de validación se muestran en el formulario y, si son generales,
  también con SweetAlert.
- La librería se vendoriza en `static/js` para no depender de un CDN.

### 6.3 Paginación

- Listados con `paginate_by = 7`, máximo 7 filas por página.
- Controles de página al pie, junto al contador de registros.
- La búsqueda y el filtro se conservan al cambiar de página.

### 6.4 Exportación a Excel

- Formato `.xlsx`, generado con `openpyxl`.
- Un `ExportarExcelMixin` que reutiliza el mismo `get_queryset()` de la vista.
- Respeta el filtro de búsqueda y exporta todas las páginas, no solo la actual.
- Sin búsqueda: exporta todos los registros.
- Con búsqueda: exporta todos los registros que calzan con el filtro.
- El botón "Exportar" va junto al de "Nuevo" en la cabecera del listado.

### 6.5 Búsqueda de vecino

- Un solo campo: por RUT (normalizado) o por nombre y apellido.
- El resultado muestra los datos del vecino y su historial; si no existe, se
  ofrece crearlo y se vuelve a Crear Atención con el vecino ya elegido.

---

## 7. Flujo "Crear Atención" (rol Funcionario)

1. El funcionario entra a "Crear Atención".
2. Un solo campo busca por RUT, nombre o apellido.
3. Si el vecino existe, se muestran sus datos y su historial de atenciones.
4. Con el vecino a la vista, el funcionario completa tipo, subatención, motivo y
   detalle, y registra la atención.
5. Si no existe, se ofrece agregarlo; al guardarlo se vuelve a Crear Atención con
   el vecino ya elegido.
6. El vecino queda asociado a la delegación del funcionario como territorio.

---

## 8. Plan por fases

- Fase A — Modelo v2. `Atencion`, `Delegacion.responsable` y tablas de la ley,
  con migraciones y registro en el Admin.
- Fase B — Reglas transversales. Mixin de regex, paginación, SweetAlert y export
  a Excel, una sola vez en `apps/common`.
- Fase C — Mantenedores. Se aplican las reglas a los siete CRUD, y la delegación
  pasa a pedir nombre y responsable.
- Fase D — Crear Atención. Flujo del funcionario e historial de vecino.
- Fase E — Ley 21.719. Registro ARCOP, auditoría, incidentes y política de
  privacidad.
- Fase F — Dashboard por rol. Estadísticas y accesos según el rol. Es lo último
  porque todavía no hay datos que mostrar. No incluye cumplimiento trimestral.

---

## 9. Decisiones

- Identificación de rol: `Rol` suma `codigo` estable y el código ramifica por él.
- `RegistroAuditoria`: escrituras siempre, más accesos y exportaciones a `Vecino`
  y `Atencion`.
- Tablas de la ley: se exponen solo en el Admin, no como CRUD del front.
- `SolicitudTitular`: la gestiona solo el administrador.
- SweetAlert: vendorizado en `static/js`.

---

## 10. Fuentes

- Ley 21.719, texto oficial: <https://www.bcn.cl/leychile/navegar?idNorma=1209272>
- EIPD Chile, explicación de la ley: <https://eipd.cl/ley-21719-explicada>
- PrivacidadWeb, guía 2026: <https://www.privacidadweb.cl/aprende/ley-21719>
