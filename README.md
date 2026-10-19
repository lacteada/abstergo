# Abstergo — Sistema Municipal de Gestión de Atención Ciudadana

Aplicación Django para la gestión de atención ciudadana de las delegaciones
municipales de La Serena. Los datos viven en una base de datos relacional y el
sistema se administra desde Django Admin y desde un front-end propio con CRUD,
con un dialogo de contexto por delegación.

Repo: https://github.com/lacteada/abstergo

## Integrantes

- _(completar con el nombre y correo de cada integrante del equipo)_

## Descripción

El sistema registra la atención entregada a los vecinos, administra las
delegaciones, los usuarios y roles, las metas por territorio y los catálogos de
tipos y sub atenciones. Cada perfil ve y edita solo lo que su rol y su contexto
de delegación autorizan.

## Estado de cada módulo

| Módulo | Estado | Notas |
|---|---|---|
| Login | Operativo | Ingreso por correo y contraseña, con bloqueo y reactivación |
| Recuperación de contraseña | Operativo | Código de 6 dígitos, vigencia configurable y espera entre reenvíos |
| CRUD Delegaciones | Operativo | Código, nombre, dirección, comuna, responsable y estado |
| CRUD Roles | Operativo | Código, nombre y descripción; permisos según la matriz |
| CRUD Usuarios | Operativo | Rol, delegación principal, delegaciones autorizadas y estado |
| CRUD Ítems y metas | Operativo | Código, nombre, descripción, delegación y estado |
| CRUD Tipo de Atención | Operativo | Código, nombre, descripción y estado |
| CRUD Sub Atención | Operativo | Código, nombre, tipo asociado y estado |
| Ingreso de atención | Operativo | Dependencia tipo → subatención, delegación del contexto e identificador |
| Consulta de registros | Operativo | Ficha de solo lectura en cada mantenedor |
| Exportar a Excel | Operativo | Respeta el filtro y todas las páginas |
| Dashboard por rol | Parcial | Estadísticas y accesos según el rol |
| API v1 (cliente móvil) | Operativo | JWT, CRUD y recuperación; esquema en `/api/docs/` |
| Ley 21.719 | Parcial | Modelos implementados; gestión desde el Admin |

## Stack

- Python 3.14 · Django 6.1
- MariaDB, driver `mysqlclient`
- `gunicorn` para producción
- `openpyxl` para la exportación a Excel
- `djangorestframework` + JWT para la API

## Requisitos

- Python 3.14
- MariaDB y sus librerías de desarrollo (el orden importa: `mysqlclient`
  compila contra sus headers).

## Instalación

1. Requisitos del sistema:

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

## Configuración

Toda la configuración sale del `.env` (ver `.env.example`): base de datos,
correo, vigencia del código OTP y espera entre reenvíos, longitud mínima de la
contraseña, y parámetros de la API. Los secretos no se versionan.

## Despliegue

Servicios, configuración y pasos de actualización en
`documentacion/despliegue_aws.md`. Resumen: Apache como frontal, gunicorn como
servidor WSGI, MariaDB como base de datos y systemd para mantener el servicio.

## Pruebas

Automatizadas (funcionales y unitarias):

```bash
bash scripts/verificar.sh        # check, migraciones, carga, ruff y pytest
```

El registro de resultados, con requisito, evidencias y el detalle de la prueba
de estrés, está en `documentacion/pruebas.md`.

Prueba de carga contra el entorno desplegado:

```bash
python scripts/estres.py --url http://18.209.251.129 --ruta /login/ \
    --niveles 5,10,20,40 --duracion 20 --salida documentacion/pruebas.md
```

## Estructura

```text
abstergo/
├── config/           settings, urls, wsgi
├── apps/
│   ├── common/       vistas base, formularios, estados, delegaciones, borrado lógico
│   ├── cuentas/      Rol, Usuario, autenticación
│   ├── organizacion/ Delegacion
│   ├── catalogos/    Meta, TipoAtencion, SubAtencion
│   ├── ciudadanos/   Vecino
│   ├── atenciones/   Atencion
│   ├── cumplimiento/ tablas de la Ley 21.719
│   ├── api/          API v1 (DRF)
│   └── panel/        Inicio, contexto de delegación y comando cargar_datos
├── datos_nuevos/     JSON de importación, uno por entidad
├── templates/        armazón, listados, formularios, consulta y acceso
├── static/           css, js, img
├── scripts/          verificar.sh, estres.py
└── documentacion/    visión, documento técnico, pruebas y despliegue
```

## Documentación

En `documentacion/`:

- `vision.md` — visión y especificación.
- `documento_tecnico.md` — documento técnico.
- `pruebas.md` — registro de pruebas funcionales y de estrés.
- `despliegue_aws.md` — servicios, configuración y pasos de despliegue.
- `prompts.md` — evidencia de uso de IA.
