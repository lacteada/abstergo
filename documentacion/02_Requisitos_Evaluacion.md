# Evaluación Sumativa #2 (25%) — Aplicación Web con Django Admin

**Asignatura:** Programación Back End (TI3041) · **Carrera:** Ingeniería en Informática / Analista Programador
**Sede:** La Serena · **Docente:** Alex Díaz Araos · **Puntaje máximo:** 100 pts
**Aprendizaje esperado:** 2.1 Codifica aplicaciones web para proponer soluciones tentativas a una problemática, utilizando un framework del lado del servidor y herramientas de inteligencia artificial como apoyo al desarrollo.

---

## Contexto y objetivo

Continuar el proyecto de la Evaluación Sumativa N°1 (sitio Django modular con dos apps que leían JSON) y transformarlo en una aplicación funcional con:
- Persistencia en base de datos relacional (migrando desde JSON).
- Administración completa vía Django Admin.
- CRUD funcional (revisado exclusivamente desde Django Admin en esta evaluación).
- Despliegue en una instancia EC2 de AWS.
- Control de versiones con Git/GitHub.

La solución debe estar **completamente operativa al momento de la revisión presencial**.

---

## Categorías de requisitos y puntos a cubrir

### 1. Infraestructura AWS EC2 — 15 pts
- Instancia EC2 con sistema operativo Linux.
- Python instalado.
- Entorno virtual operativo.
- Django Framework instalado.
- Servidor web ejecutando la aplicación.
- Git instalado.
- Base de datos operativa.
- **Durante la revisión, demostrar:**
  - Conexión a la instancia EC2.
  - Ejecución del proyecto desde la instancia.
  - Funcionamiento de la aplicación en vivo.

### 2. Control de versiones (Git y GitHub) — 10 pts
- Repositorio GitHub propio.
- Historial de commits asociado al desarrollo.
- Configuración del repositorio remoto.
- Clonación del proyecto desde GitHub hacia EC2 mediante `git clone URL_DEL_REPOSITORIO`.
- **Evidencias mínimas:** repositorio remoto visible + historial de commits + clonación demostrada en vivo.

### 3. Variables de entorno — 10 pts
- Las configuraciones sensibles **no** pueden estar escritas directamente en el código.
- Deben cargarse desde un archivo de variables de entorno mediante librerías apropiadas.

### 4. Modelado de datos con Django ORM — 20 pts
- Migración completa de la información desde JSON hacia base de datos relacional.
- Modelo de datos propio del estudiante, con todas las entidades necesarias para su problemática (no hay mínimo de tablas, pero deben implementarse **todas** las contempladas en el diseño).
- Uso de:
  - Modelos Django.
  - Relaciones entre entidades.
  - Llaves foráneas (`ForeignKey`) cuando corresponda.
  - Migraciones.
  - Consultas ORM.
- **Evidencias mínimas:** archivos de migraciones + explicación de entidades creadas, relaciones existentes y finalidad de cada tabla.
- **Verificación cruzada (docente valida consistencia entre):** modelos Django ↔ migraciones ↔ base de datos ↔ phpMyAdmin.
  - Desde Django: modelos implementados, migraciones ejecutadas, registros creados vía Django Admin.
  - Desde phpMyAdmin: existencia física de tablas, estructura de tablas, relaciones implementadas, registros almacenados.

### 5. Django Admin — 15 pts
- Todas las entidades del modelo deben estar registradas y operativas en Django Admin (no se acepta modelo sin administración en Admin).
- Funcionalidades mínimas desde Django Admin:
  - Crear registros.
  - Modificar registros.
  - Eliminar registros.
  - Visualizar registros.
  - Buscar registros.
  - Navegar entre entidades relacionadas.
- La revisión de CRUD se hace **exclusivamente** a través del panel de Django Admin en esta evaluación.

### 6. Front End — visualización de datos — 20 pts
- Vistas construidas con plantillas Django, obteniendo datos mediante Django ORM (no acceso directo a JSON).
- Cada módulo del sistema debe tener una vista de listado de sus registros (ej.: productos, categorías, clientes, reservas, videojuegos, películas, o la temática propia del estudiante).
- La información debe presentarse mediante: tablas HTML, tarjetas, o listas estructuradas.
- **Navegación:** enlaces de acceso a los distintos módulos del sistema.
- **Botones de acción por vista de listado** (deben existir visualmente, no requieren estar operativos aún):
  - Botón Agregar.
  - Botón Modificar.
  - Botón Eliminar.
  - Botón Buscar.
  - Deben existir visualmente, mantener estructura coherente y enlazar a una ruta o marcador de posición.
  - **No** es requisito que ejecuten acciones reales, modifiquen datos, ni que estén operativos (esa parte se evalúa en la evaluación sumativa siguiente).

### 7. Evidencia de uso de Inteligencia Artificial — 5 pts
- Prompts utilizados.
- Respuestas obtenidas.
- Aplicación de esas respuestas en el desarrollo del proyecto.

### 8. Documentación técnica — 5 pts
Entregar documento técnico (PDF o Word) completo y organizado, que incluya:
- **Descripción del proyecto:** objetivo, temática elegida, funcionalidades implementadas.
- **Arquitectura:** estructura de carpetas, aplicaciones desarrolladas, base de datos utilizada.
- **Evidencia AWS:** capturas de instancia EC2, terminal Linux, ejecución del proyecto.
- **Evidencia GitHub:** capturas de repositorio, commits, clonación del proyecto.
- **Evidencia Base de Datos:** capturas de modelos Django, migraciones, tablas creadas.
- **Evidencia phpMyAdmin:** capturas de existencia de tablas, registros almacenados, relaciones implementadas.
- **Evidencia de IA:** prompts, respuestas, aplicación de las respuestas.

---

## Checklist de revisión presencial obligatoria

**Infraestructura**
- [ ] Conexión a EC2
- [ ] Proyecto clonado desde GitHub
- [ ] Entorno virtual activo

**Base de Datos**
- [ ] Todos los modelos creados
- [ ] Migraciones aplicadas
- [ ] Tablas visibles en phpMyAdmin
- [ ] Registros almacenados

**Django Admin**
- [ ] Administración de todas las entidades
- [ ] Creación de registros
- [ ] Edición de registros
- [ ] Eliminación de registros
- [ ] Búsqueda de registros

**Front End**
- [ ] Listados construidos desde datos almacenados en la base de datos
- [ ] Uso de Django ORM
- [ ] Tablas o vistas de visualización funcionando
- [ ] Botones Agregar, Modificar, Eliminar y Buscar visibles en la interfaz

**Control de Versiones**
- [ ] Repositorio GitHub
- [ ] Historial de commits
- [ ] Clonación del proyecto desde GitHub hacia EC2

---

## Entregables

1. **Proyecto Django desplegado en AWS**, ejecutándose desde EC2, con base de datos funcional, CRUD operativo (vía Admin) y administrador Django operativo.
2. **Repositorio GitHub** con código fuente completo, historial de desarrollo, archivo `README`, archivo `.gitignore` adecuado.
3. **Documento técnico (PDF o Word)** con el contenido detallado en la sección 8.

---

## Pauta de evaluación (resumen de puntajes)

| Criterio | Puntaje máx. |
|---|---|
| Configuración EC2 y despliegue de la app Django | 15 |
| Uso de Git y GitHub (repo, commits, clonación) | 10 |
| Variables de entorno para configuración sensible y BD | 10 |
| Modelos Django ORM (entidades, relaciones, migraciones) | 20 |
| Administración de entidades vía Django Admin (CRUD) | 15 |
| Visualización de datos vía templates Django + ORM | 20 |
| Evidencia de uso de herramientas de IA | 5 |
| Documentación técnica completa | 5 |
| **Total** | **100** |

**Niveles de logro:** Logrado (L) = 100% · Medianamente Logrado (ML) = 70% · Por Lograr (PL) = 40% · No Logrado (NL) = 0%.
