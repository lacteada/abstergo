# Plan de Proyecto — Sistema Municipal de Gestión de Atención Ciudadana

Documento de planificación. Define el alcance, el modelo de datos, las fases de trabajo y la estrategia de Git antes de escribir código.

**Estado de partida:** el repositorio no tiene commits, no hay código Django y `requirements.txt` está vacío. Solo existen los documentos `00` a `05`.

---

## 1. Objetivo

Convertir el proyecto de la Evaluación 1 (que leía datos desde JSON) en una aplicación Django funcional con base de datos relacional, administrada por Django Admin, desplegada en EC2 y versionada en GitHub, completamente operativa en la revisión presencial.

## 2. Alcance

Incluye:

- Modelo de datos propio con 7 entidades y relaciones.
- Migración de datos desde los JSON de la Evaluación 1 mediante comando de gestión.
- Django Admin operando el CRUD completo de todas las entidades.
- Front-end con plantillas Django, listados, buscador y botones de acción funcionales.
- Autenticación propia con OTP, más el login de Django Admin.
- Reportes como vista de solo lectura.
- Despliegue en EC2 con MariaDB y phpMyAdmin accesibles.
- Documento técnico con capturas y evidencia de IA.

No incluye:

- API REST ni SPA.
- Migración de Compromisos y Actividades (decidido en la problemática 13).
- Entidades sin pantalla detallada en el mockup.

## 3. Mapa de puntajes

- **Modelos ORM (20 pts):** 7 entidades, relaciones, `ForeignKey` con `PROTECT` o `SET_NULL`, migraciones y consultas ORM.
- **Front-end (20 pts):** una vista de listado por módulo, tablas HTML, navegación entre módulos y botones Agregar, Modificar, Eliminar y Buscar.
- **EC2 (15 pts):** instancia Linux, Python, entorno virtual, Django, servidor web y base de datos operativos.
- **Django Admin (15 pts):** las 7 entidades registradas, con crear, editar, eliminar, ver, buscar y navegar relaciones.
- **Git/GitHub (10 pts):** repositorio propio, historial de commits y clonación demostrada en el EC2.
- **Variables de entorno (10 pts):** configuración sensible fuera del código.
- **Evidencia IA (5 pts):** prompts, respuestas y su aplicación.
- **Documento técnico (5 pts):** PDF o Word completo.

## 4. Modelo de datos

Entidades y campos derivados de los mockups:

- **Rol** — nombre, descripción.
- **Usuario** — nombre, correo, rol, estado. Sobre `auth.User` con perfil, y `Groups` como Roles.
- **Delegación Municipal** — nombre, dirección, comuna.
- **Meta** — nombre, descripción.
- **Tipo de Atención** — nombre, descripción.
- **Sub Atención** — nombre, llave foránea a Tipo de Atención.
- **Vecino** — nombre, RUT, dirección, teléfono, territorio, tipo de gestión, estado.

Decisiones asociadas:

- `territorio` es llave foránea a Delegación, con `PROTECT`. Los datos de la Evaluación 1 ya usan nombres de delegación.
- `tipo de gestión` es texto libre, para no sumar entidades.
- `estado` se maneja con valores Activo e Inactivo y color semántico verde o rojo.
- Ninguna llave foránea borra en cascada.

## 5. Fases del trabajo

**Fase 0 — Repositorio y esqueleto**
- Primer commit con documentos, `README`, `.gitignore` y `requirements.txt`.
- Crear el proyecto Django y la app principal con `manage.py startapp`.
- Definir la estructura: `config/` para settings y `apps/` para los módulos.

**Fase 1 — Modelos y migraciones**
- Escribir los 7 modelos con sus relaciones.
- Generar y aplicar migraciones.
- Registrar todo en Django Admin.

**Fase 2 — Admin operativo**
- `list_display`, `search_fields` y filtros por entidad.
- Verificar crear, editar, eliminar, buscar y navegar relaciones.

**Fase 3 — Migración desde JSON**
- Comando de gestión que lee `usuarios.json` y `delegaciones.json` de `Abstergo2` e inserta vía ORM, reejecutable sin duplicar.
- Datos de ejemplo para las entidades sin origen.

**Fase 4 — Front-end**
- Portar el diseño de laserena.cl a plantillas Django: navbar, tipografía, tablas, breadcrumb y botones.
- Sobrescribir `--muni-base` y los rojos fijos con la paleta institucional.
- Patrón único de listado: título, buscador, botón "Nuevo", tabla y columna de acciones.

**Fase 5 — Autenticación**
- Login, recuperar contraseña, OTP de 6 dígitos y nueva contraseña.
- Configurar el envío de correo por variables de entorno.
- Un super admin del sistema, independiente del Admin.

**Fase 6 — Reportes**
- Vista de solo lectura con tablas agregadas por tipo y estado.

**Fase 7 — Despliegue en EC2**
- Instalar MariaDB, librerías de desarrollo y `mysqlclient`.
- Instalar phpMyAdmin y habilitar `mod_proxy` en Apache.
- Configurar gunicorn y enrutar Django por reverse proxy.
- Clonar el repositorio en la instancia y cargar el `.env`.

**Fase 8 — Documentación**
- Capturas de EC2, terminal, GitHub, ORM, migraciones y phpMyAdmin.
- Redactar el documento técnico y exportarlo a PDF.
- Recopilar prompts y respuestas para la evidencia de IA.

## 6. Estrategia de Git

- Rama `main` como única rama estable; el trabajo avanza con commits frecuentes por hito, no con ramas largas.
- El primer commit deja el repositorio con la documentación y los archivos base.
- Un commit por unidad terminada: modelos, migraciones, admin, comando de importación, plantillas, autenticación, despliegue.
- Mensajes en imperativo y en español, con alcance claro.
- `.gitignore` ya excluye `venv/`, `.env`, `*.pem`, cachés, `db.sqlite3`, `staticfiles/` y `media/`.
- La llave SSH vive en `~/.ssh/abstergo-key.pem`, fuera del repositorio.
- Antes de cada commit, comprobar con `git add -n .` que no se cuele ningún archivo sensible.

## 7. Dependencias y entorno

`requirements.txt` debe declarar, como mínimo:

- `Django`
- `mysqlclient`
- `django-environ`
- `gunicorn`

El `.env` debe contener la clave secreta, el modo de depuración, los hosts permitidos y las credenciales de MariaDB.

## 8. Riesgos y mitigaciones

- **Migración incompleta:** dos de los cuatro JSON quedan sin destino. Mitigación: documentarlo como decisión y poblar por comando o por Admin.
- **Modelo más corto que el diseño:** el mockup nombró entidades sin pantalla. Mitigación: justificar que solo se implementan las detalladas.
- **OTP sin correo saliente:** puede fallar en la demo. Mitigación: dejar el correo configurable y probar el envío antes de la revisión.
- **phpMyAdmin expuesto en EC2:** riesgo de seguridad. Mitigación: restringir el acceso por ruta o por origen.
- **Tiempo:** las fases 5 y 7 son las más costosas. Mitigación: dejar el CRUD y los listados operativos antes de refinar la autenticación.

## 9. Checklist de la revisión presencial

- Conexión a EC2 y entorno virtual activo.
- Proyecto clonado desde GitHub.
- Migraciones aplicadas y tablas visibles en phpMyAdmin.
- Registros almacenados.
- CRUD completo por Django Admin.
- Listados del front leyendo desde ORM.
- Botones Agregar, Modificar, Eliminar y Buscar visibles en cada listado.
- Historial de commits y clonación demostrable.
