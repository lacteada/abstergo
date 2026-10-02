# Abstergo — Sistema Municipal de Gestión de Atención Ciudadana

Aplicación Django para la gestión de atención ciudadana de las delegaciones
municipales. Los datos viven en una base de datos relacional y el sistema se
administra desde Django Admin, con un front-end de listados y CRUD sobre
plantillas Django.

Repo: https://github.com/lacteada/abstergo

## Qué incluye

- 7 entidades con ORM y migraciones.
- Comando de carga de datos desde JSON, idempotente.
- Django Admin con las 7 entidades, con CRUD y borrado normal.
- Front-end: los 7 listados con alta, edición y borrado lógico, más búsqueda en vivo.
- Autenticación: login, recuperar contraseña, código OTP y nueva contraseña.

## Stack

- Python 3.14 · Django 6.1
- MariaDB, driver `mysqlclient`
- `gunicorn` para producción

## Estructura

```text
abstergo/
├── config/           settings, urls, wsgi
├── apps/
│   ├── common/       vistas base, Admin base (CRUD), borrado lógico
│   ├── cuentas/      Rol, Usuario, autenticación
│   ├── organizacion/ Delegacion
│   ├── catalogos/    Meta, TipoAtencion, SubAtencion
│   ├── ciudadanos/   Vecino
│   └── panel/        Inicio y comando cargar_datos
├── datos_nuevos/     JSON de importación, uno por entidad
├── templates/        armazón, listados y pantallas de acceso
├── static/           css, js, img
└── documentacion/    planificación, traslado, prompts y documento técnico
```

## Puesta en marcha

1. Requisitos del sistema: MariaDB y sus librerías de desarrollo. El orden
   importa: `mysqlclient` compila contra los headers de MariaDB.

   ```bash
   sudo pacman -S mariadb        # o el gestor de paquetes de tu distro
   ```

2. Entorno virtual y dependencias:

   ```bash
   python -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   pip install mysqlclient        # después de instalar MariaDB
   ```

3. Variables de entorno: copiar `.env.example` a `.env` y completar las
   credenciales.

4. Base de datos y datos:

   ```bash
   python manage.py migrate
   python manage.py cargar_datos   # lee datos_nuevos/; reejecutable sin duplicar
   python manage.py runserver
   ```

## Documentación

En `documentacion/`:

- `documento_tecnico.md` — documento técnico (se exporta a PDF).
- `prompts.md` — evidencia de uso de IA.
- `traslado_de_datos.md` — mapeo del JSON de origen a las tablas.
