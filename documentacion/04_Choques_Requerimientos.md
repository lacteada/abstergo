# Choques de Requerimientos y Opciones de Solución

## Fuentes

- `00_Analisis_Frontend.md` — análisis del front-end de laserena.cl, sitio de referencia.
- `01_Diseno_Mockups.md` — mockups del sistema.
- `02_Requisitos_Evaluacion.md` — pauta de la Evaluación Sumativa #2.
- `03_Normas_Graficas.md` — identidad visual oficial.
- Proyecto de la Evaluación 1 — `/home/lct/code/ina/backend/Abstergo2` (código y datos JSON).

Cada problemática trae sus opciones con ventajas y costos, y la **Decisión** ya resuelta.

## Resumen de decisiones

- El front-end moldea el diseño scrapeado de laserena.cl dentro de plantillas Django.
- Paleta institucional, con `#C41230` como color primario.
- Modelo de 7 entidades: Delegaciones Municipales, Usuarios, Roles, Metas, Tipo de Atención, Sub Atención y Vecinos.
- Llaves foráneas con `PROTECT` o `SET_NULL`: nada en cascada sobre datos.
- MariaDB en el EC2, con credenciales en `.env`.
- Apache sirve phpMyAdmin y enruta Django a gunicorn por reverse proxy.
- Front con CRUD funcional y Django Admin también funcional.
- Autenticación propia con OTP, más el login de Django Admin.
- Migración por comando de gestión desde los JSON de la Evaluación 1.
- Reportes como vista de solo lectura.
- Entregable en Markdown, convertido a PDF con capturas.

**Decisiones que se anulan entre sí:** la 10b reemplaza a la 1, y la 13 reemplaza a la 5.

---

## 1. Alcance del CRUD

**Choca:** la pauta exige que el CRUD se revise solo por Django Admin; los mockups muestran botones "+ Nuevo", lápiz y basurero en cada listado.

- **Opción A — Solo Admin, botones inertes.** Los botones del front existen y apuntan a `#`. Cumple la pauta al pie de la letra, cero riesgo, cero tiempo extra.
- **Opción B — Admin + CRUD funcional en el front.** Formularios Django reales sobre los listados. Suma robustez y sirve para la evaluación siguiente, pero no puntúa ahora y consume tiempo.
- **Opción C — Admin + botones que avisan.** El front abre un aviso de "disponible en la próxima entrega". Mantiene la apariencia del mockup y deja claro el alcance.

**Decisión (anulada):** originalmente Opción A, pero la problemática 10b la reemplazó. El front tendrá CRUD funcional y Django Admin también operará.

---

## 2. Autenticación y código OTP

**Choca:** los mockups definen login, recuperar contraseña, OTP de 6 dígitos y nueva contraseña; la pauta no pide autenticación y Django Admin ya trae su propio login.

- **Opción A — Sin flujo propio.** Se entra por el login de Django Admin. Cumple la pauta, descarta 4 pantallas del mockup.
- **Opción B — Login propio sin OTP.** Plantilla que imita el mockup sobre `django.contrib.auth`. Mantiene la apariencia, evita el correo saliente.
- **Opción C — Flujo completo con OTP.** Requiere SMTP o SES en el EC2, almacenar códigos y temporizadores. Máxima fidelidad al mockup, mayor riesgo, no puntúa.

**Decisión:** Opción C. Se implementan las cuatro pantallas (login, recuperar contraseña, OTP de 6 dígitos, nueva contraseña). Implica configurar envío de correo saliente y guardar códigos con expiración.

---

## 3. Enfoque del front-end

**Choca:** el análisis describe una SPA en React con Vite; la pauta exige plantillas Django con ORM.

- **Opción A — Plantillas Django + Bootstrap por CDN.** Un patrón de listado reutilizable para todos los mantenedores. Cumple la pauta y es la vía más rápida.
- **Opción B — Plantillas Django + CSS propio.** Se inspira en el portal (barra lateral, `.titulo`, colores institucionales). Más fiel al look municipal, algo más de trabajo.
- **Opción C — SPA aparte contra una API.** Viola el requisito de plantillas + ORM. Descartada.

**Decisión:** Se moldea el diseño scrapeado de laserena.cl dentro de plantillas Django: clases y tokens de `frameworkV1.css` (navbar `bg-muni`, tipografía del sistema, tablas, breadcrumb, botones `btn-muni`), reescritos como templates.

**Advertencia:** laserena.cl no usa sidebar; su armazón es navbar horizontal con carrusel. El armazón del sistema (sidebar + header) viene de los mockups, y de laserena.cl se reutiliza el lenguaje visual (colores, botones, tablas, tipografía).

---

## 4. Paleta y color primario

**Choca:** el mockup pide botón primario azul; las normas gráficas fijan el rojo heráldico como principal; el portal real usa `#AD0000`.

- **Opción A — Manual institucional.** Primario `#C41230`, apoyo `#DB3334` y `#8B1D19`. Coherente con "municipal" y con el documento de normas.
- **Opción B — Igualar el portal.** Primario `#AD0000`, para parecerse al sitio en producción, aunque el sitio incumpla su propio manual.
- **Opción C — Azul del mockup.** Ignora el manual. Solo válida si el mockup manda sobre la identidad.

**Nota:** en cualquier caso se mantiene verde/rojo para los estados Activo/Inactivo.

**Decisión:** Opción A. Primario `#C41230`, con `#DB3334` y `#8B1D19` de apoyo. Como el framework scrapeado está construido sobre `#AD0000`, hay que sobrescribir la variable `--muni-base` y los rojos fijos del CSS.

---

## 5. Entidades que el diseño no define

**Choca:** la pauta obliga a implementar todas las entidades del diseño, pero "Atenciones" y "Tipo de Gestión" no tienen columnas y "Territorio" no tiene mantenedor.

- **Opción A — Modelado mínimo razonable.** Atención: fecha, vecino, tipo, sub atención, estado, observación. Tipo de Gestión: nombre, descripción. Territorio: nombre. Se documenta como decisión propia.
- **Opción B — Solo lo definido.** Se implementa únicamente lo que el mockup detalla y se omiten las tres. Riesgo de incumplir "todas las del diseño".
- **Opción C — Reinterpretar.** Territorio pasa a ser la Delegación o la Comuna, y Atención queda como cabecera del sistema. Menos tablas, más acoplamiento.

**Decisión:** Opción A. Modelado mínimo: Atención (fecha, vecino, tipo, sub atención, estado, observación), Tipo de Gestión (nombre, descripción) y Territorio (nombre).

**Revisión:** la problemática 13 deja esta decisión sin efecto, porque limita el modelo a las entidades con pantalla detallada.

---

## 6. Módulo Reportes

**Choca:** la pauta exige una vista de listado por cada módulo; Reportes aparece en el sidebar pero no es una entidad con registros.

- **Opción A — Vista de solo lectura.** Tablas agregadas por tipo y estado, sin modelo nuevo.
- **Opción B — Solo el enlace.** Se deja el ítem en el sidebar sin vista.
- **Opción C — Modelo Reporte.** Entidad con fecha, tipo y autor, más su CRUD en Admin.

**Decisión:** Opción A. Vista de solo lectura con tablas agregadas por tipo y estado, sin modelo nuevo.

---

## 7. Servidor web para Django

**Choca:** la pauta pide un servidor web ejecutando la aplicación; el README instaló un stack LAMP para PHP y nada para servir Django.

- **Opción A — gunicorn + nginx.** Estándar de producción. Requiere instalar y configurar nginx.
- **Opción B — gunicorn + Apache mod_wsgi.** Reutiliza el `httpd` ya instalado; evita sumar otro servidor.
- **Opción C — `runserver 0.0.0.0:8000`.** Lo más simple, pero no es un servidor web real y puede no convencer al docente.

**Decisión:** Se usa el Apache ya instalado como único servidor y se montan los dos servicios a la vez: phpMyAdmin servido con PHP y el proyecto Django enrutado a gunicorn por reverse proxy. Requiere instalar phpMyAdmin y habilitar `mod_proxy`.

---

## 8. Base de datos y configuración por entorno

**Choca:** phpMyAdmin implica MySQL/MariaDB; `requirements.txt` está vacío, Django por defecto usa SQLite y aún no hay carga por variables de entorno.

- **Opción A — MariaDB en el EC2.** Con `mysqlclient`, credenciales en `.env` y `django-environ`. Es lo que phpMyAdmin puede verificar.
- **Opción B — SQLite.** Trivial de levantar, pero phpMyAdmin no verá tablas: incumple la verificación cruzada.
- **Opción C — MySQL en RDS.** Más cercano a producción, con costo y configuración de red.

**Nota:** `mysqlclient` necesita las librerías de desarrollo de MariaDB en el EC2.

**Decisión:** Opción A. MariaDB en el EC2, `mysqlclient` como driver y credenciales en `.env` con `django-environ`.

---

## 9. Migración desde JSON

**Choca:** la pauta pide migrar la información de la Evaluación 1 desde JSON, pero varias entidades nuevas no tienen datos de origen.

- **Opción A — Comando de gestión.** Un `importar_json` que lee los JSON e inserta vía ORM, reejecutable sin duplicar.
- **Opción B — Fixtures.** Archivos `loaddata` de Django. Simple, pero menos claro como evidencia de migración.
- **Opción C — Carga manual.** Se registra todo por Admin y se documenta. Rápido, pero no demuestra migración.

**Decisión:** Opción A. Comando de gestión que lee los JSON del proyecto de la Evaluación 1 e inserta vía ORM. Los archivos de origen existen y se leen directo del proyecto anterior.

---

## 10. Usuarios y Roles

**Choca:** el mockup pide CRUD de Usuarios con Rol, pero Django ya trae `User` y `Groups`.

- **Opción A — `auth.User` + `Groups` + perfil.** Una sola fuente de verdad; el perfil aporta los campos extra.
- **Opción B — Modelo `Usuario` propio.** Fiel al mockup, pero duplica el sistema de autenticación.
- **Opción C — Solo `auth.User`.** Sin Roles: se usan `is_staff` e `is_active`. Lo más simple, se aleja del mockup.

**Decisión:** Dos accesos activos y ambos funcionales. Django Admin con su login propio operando el CRUD completo, y el acceso del sistema según el mockup con un único super admin que recupera cuenta y usa el CRUD del front.

**Choque detectado:** esta decisión anula la de la problemática 1 (botones inertes).

---

## 11. Menú del sidebar en el mockup

**Choca:** la sección 0.1 lista 9 sub-ítems; la sección 11 habla de dos adicionales ("Atenciones" y "Tipo de Gestión").

- **Opción A — Lista ampliada.** Se adoptan los 11 sub-ítems y se corrige la sección 0.1 del mockup.
- **Opción B — Lista corta.** Se dejan 9 y se eliminan Atenciones y Tipo de Gestión.
- **Opción C — Lista corta con reserva.** Se dejan 9 y los dos restantes quedan anunciados para la próxima entrega.

**Decisión:** Manda el mockup detallado, no el listado del sidebar. El grupo Mantenedores queda con 7 ítems: Delegaciones Municipales, Usuarios, Roles, Metas, Tipo de Atención, Sub Atención y Vecinos. Atenciones y Tipo de Gestión salen del menú; Tipo de Gestión sigue existiendo como columna de Vecinos.

---

## 12. Documento técnico, capturas y evidencia de IA

**Choca:** la pauta exige PDF o Word con capturas y evidencia de IA; los insumos están en Markdown y las capturas aún no existen.

- **Opción A — Markdown y exportación.** Se redacta en Markdown y se convierte a PDF al final; las capturas se toman del sistema ya desplegado.
- **Opción B — Word directo.** Se redacta en Word desde el inicio. Menos fricción final, menos reutilizable.
- **Opción C — Híbrido.** Markdown durante el desarrollo y conversión con capturas en la última etapa.

**Nota:** la evidencia de IA exige guardar prompts y respuestas, así que conviene exportarlos antes de cerrar la sesión de trabajo.

**Decisión:** Opción A. Se redacta en Markdown y se exporta a PDF al final, con las capturas tomadas del sistema ya desplegado en el EC2.

---

## 13. Datos de la Evaluación 1 contra las entidades del mockup

**Choca:** los JSON de la Evaluación 1 contienen **Compromisos** y **Actividades**; las entidades del mockup son Vecinos, Metas, Tipo de Atención y Sub Atención. Solo Usuarios y Delegaciones coinciden en ambos mundos.

- **Opción A — Reinterpretar y migrar todo.** Compromiso pasa a ser Atención y Actividad pasa a ser evidencia de gestión; las entidades sin origen se pueblan con datos de ejemplo.
- **Opción B — Migrar solo las coincidencias.** Se migran Usuarios y Delegaciones y el resto se llena con datos de ejemplo.
- **Opción C — Mantener ambas estructuras.** Se conservan tablas propias de la Evaluación 1 y además las del mockup.

**Datos de origen detectados en `Abstergo2`:** 8 compromisos con historial de estados (INGRESADO, PENDIENTE, EN_PROCESO, REALIZADO), evidencias de actividad con estados VALIDADO, PENDIENTE y RECHAZADO, usuarios y delegaciones. Territorios presentes en los datos: centro, rural, avenida-del-mar, la-antena, las-companias, la-pampa.

**Decisión:** Se conservan solo las entidades del mockup que están individualmente detalladas: Delegaciones Municipales, Usuarios, Roles, Metas, Tipo de Atención, Sub Atención y Vecinos. Compromisos y Actividades no se migran por no tener equivalente; la migración queda cubierta por Usuarios y Delegaciones.

**Choque detectado:** esta decisión anula la de la problemática 5. Se debilita la "migración completa" que pide la pauta, porque dos de los cuatro JSON quedan sin destino.

**Regla de integridad (13b):** modelo simple y minimalista, sin entidades extra y sin borrados destructivos. Las llaves foráneas usan `PROTECT` (o `SET_NULL` si el dato es opcional), de modo que borrar un Rol, una Delegación o un Tipo de Atención no elimine ni rompa los registros dependientes. Territorio queda como llave foránea a Delegación y Tipo de Gestión como texto libre en Vecinos.

---

## Anexo. Inventario del proyecto de la Evaluación 1

Ubicación: `/home/lct/code/ina/backend/Abstergo2`.

Estructura: `manage.py`, `config/` (settings), `apps/`, `templates/`, `static/`, `db.sqlite3` y su propio `venv/`. Trae el documento `Eva Sumativa 1.md`.

Aplicaciones y datos:

- `usuarios` — `apps/usuarios/data/usuarios.json`.
- `delegacion` — `apps/delegacion/data/delegaciones.json`.
- `agenda` — `apps/agenda/data/compromisos.json`.
- `actividades` — `apps/actividades/data/actividades.json`.
- `tablero` — sin JSON asociado.

Entidades de origen:

- **Compromiso** — codigo, solicitante, territorio, responsable, fecha_compromiso, fecha_limite, estado, observacion, más un historial de cambios de estado.
- **Actividad** — codigo_evidencia, fecha, descripcion, accion, contacto, telefono, delegacion, estado, fecha_creacion.
- **Usuario** y **Delegación**.

Estados observados en los datos:

- Compromiso: INGRESADO, PENDIENTE, EN_PROCESO, REALIZADO.
- Actividad: VALIDADO, PENDIENTE, RECHAZADO.

Territorios usados como dato: centro, rural, avenida-del-mar, la-antena, las-companias, la-pampa.

Nota: en la misma carpeta `backend/` hay otros proyectos Django que no corresponden a esta evaluación: `Abstergo`, `AbstergoV1`, `DJANGO-ALEX` y `ejemplote`.
