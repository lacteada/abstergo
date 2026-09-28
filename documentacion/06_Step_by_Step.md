# 06 · Step by Step

Ejecución del `05_Plan_Proyecto.md` con el mínimo de piezas y de decisiones.

Regla: `Abstergo2` solo se lee. De ahí salen los datos de origen y nada más.

---

## Recursos mínimos

- Un solo motor de base de datos: MariaDB en local y MariaDB en el EC2. Sin SQLite.
- Vistas genéricas de Django para los 7 módulos, sin lógica escrita a mano.
- Un parcial de tabla y un parcial de formulario compartidos por los 7 módulos.
- Sin Bootstrap: el framework de laserena.cl más un CSS propio para el armazón.
- Un solo `ModelAdmin` base en solo lectura para las 7 entidades.
- Un solo comando que importa el JSON nuevo.
- `prompts.md` se extrae del historial de sesión, no se copia a mano.
- OTP guardado en la sesión: sin tabla extra y sin migración.
- PDF por impresión de VSCodium. pandoc no está instalado y no hace falta.
- Fuera del alcance: Reportes, API REST, SPA y las entidades sin pantalla detallada.
- Rama `main`, un commit por fase, `git add -n .` antes de cada uno.

---

## Setup único

Local, una sola vez. Estos comandos van con `sudo`, los corres tú.

```bash
sudo pacman -S mariadb
sudo mariadb-install-db --user=mysql --basedir=/usr --datadir=/var/lib/mysql
sudo systemctl enable --now mariadb
sudo mariadb -e "CREATE DATABASE abstergo CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"
sudo mariadb -e "CREATE USER 'abstergo'@'localhost' IDENTIFIED BY 'abstergo'; GRANT ALL PRIVILEGES ON abstergo.* TO 'abstergo'@'localhost'; FLUSH PRIVILEGES;"
```

Dependencias del proyecto. El orden importa: `mysqlclient` compila contra los headers de MariaDB, y esos headers recién existen después de instalar `mariadb`.

```bash
cd ~/code/ina/backend/abstergo
source venv/bin/activate
pip install Django python-dotenv gunicorn
pip install mysqlclient          # recién después de sudo pacman -S mariadb
pip freeze > requirements.txt
```

**Verificar**

- `systemctl is-active mariadb` responde `active`.
- `mariadb -u abstergo -pabstergo -e "SHOW DATABASES;"` lista `abstergo`.

---

## Fase 0 — Arranque

```bash
cd ~/code/ina/backend/abstergo
source venv/bin/activate
django-admin startproject config .
mkdir -p apps/common templates static/css static/js static/img datos_nuevos documentacion
touch apps/__init__.py
for a in cuentas organizacion catalogos ciudadanos panel; do python manage.py startapp $a apps/$a; done
```

**Ajustes**

- En cada `apps/<app>/apps.py`, cambiar `name = "<app>"` por `name = "apps.<app>"`.
- Registrarlas en `INSTALLED_APPS` como `"apps.cuentas"`, `"apps.organizacion"`, `"apps.catalogos"`, `"apps.ciudadanos"`, `"apps.panel"`.
- `LANGUAGE_CODE = "es"` y `TIME_ZONE = "America/Santiago"`.
- `.env` con `SECRET_KEY`, `DEBUG`, `ALLOWED_HOSTS`, `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT` y `EMAIL_BACKEND`. El `.gitignore` ya lo excluye.
- `.env.example` con las mismas llaves y valores vacíos.
- `settings.py` lee el `.env` con `python-dotenv` y arma `DATABASES` con las variables `DB_*`.
- `STATIC_URL`, `STATICFILES_DIRS` apuntando a `static/` y `STATIC_ROOT`. Sin `STATIC_ROOT`, el `collectstatic` de la Fase 5 falla.

**Verificar**

- `python manage.py runserver` levanta sin errores.
- `python manage.py check` no reporta nada.
- `git add -n .` no muestra `.env` ni `venv/`.

**Commit:** primer commit con los documentos, el `README`, el `.gitignore` y `requirements.txt`.

---

## Fase 1 — Modelos y Admin

Ninguna llave foránea borra en cascada: todas usan `PROTECT`. Para que el mantenedor pueda dar de baja una entidad en uso, las siete entidades llevan borrado lógico.

| App | Modelo | Campos |
|---|---|---|
| organizacion | Delegacion | codigo (único), nombre, direccion, comuna |
| cuentas | Rol | nombre (único), descripcion |
| cuentas | Usuario | sin `username`; email (único, nulable, `USERNAME_FIELD`), first_name, last_name, is_active, rol (`PROTECT`), delegacion (`PROTECT`) |
| catalogos | Meta | nombre, descripcion, delegacion (`PROTECT`) |
| catalogos | TipoAtencion | nombre, descripcion |
| catalogos | SubAtencion | nombre, tipo_atencion (`PROTECT`) |
| ciudadanos | Vecino | nombre, rut (único), direccion, telefono, territorio (`PROTECT`), tipo_gestion, estado |

- `Rol` es una entidad propia, con su CRUD. No se usa `auth.Group`.
- El usuario es un modelo propio (`AUTH_USER_MODEL = cuentas.Usuario`), no el `auth.User`. No hay tabla de perfil ni señal `post_save`.
- No hay `username`: la llave es un `id` propio y el correo es editable, así que cambiarlo no toca la identidad de la cuenta. El correo es además el `USERNAME_FIELD`, o sea el campo de acceso.
- `is_active` es la bandera Activo/Inactivo del usuario, porque es la que Django consulta al iniciar sesión.
- Relaciones: `Usuario` → `Rol` y → `Delegacion`, `Meta` → `Delegacion`, `SubAtencion` → `TipoAtencion` y `Vecino` → `Delegacion`.
- Las siete heredan el borrado lógico: seis de `BorradoLogico` (una columna `eliminado` con fecha, un gestor `objects` que esconde las dadas de baja, un gestor `todos` que las ve, y el método `eliminar()`), y `Usuario` solo de `Eliminado`, porque su `objects` tiene que seguir siendo un `UserManager`.
- Con el borrado lógico, el mantenedor da de baja sin que nadie pierda la referencia: el vecino sigue mostrando su territorio y el usuario su rol.
- `PROTECT` queda como red de seguridad: un `DELETE` real sobre una de ellas sigue bloqueado.
- Efecto asumido: el `codigo` de una Delegación y el `nombre` de un Rol quedan ocupados aunque estén dados de baja. Recargar el JSON los restaura.
- `Vecino.territorio` es obligatorio: un vecino siempre tiene territorio.
- El correo admite nulos: varios usuarios sin correo conviven sin chocar contra el índice único. Un usuario sin correo no puede entrar, y su contraseña queda inutilizable.
- `Meta` cuelga de `Delegacion`. Los 6 cargos de `usuarios.json` se siguen descartando, y se justifican en `documentacion/traslado_de_datos.md`.
- Los campos del modelo son el contrato del JSON nuevo de la Fase 2: se define primero la tabla y después el archivo.

Admin, escrito una sola vez:

```python
class SoloLectura(admin.ModelAdmin):
    def has_add_permission(self, request): return False
    def has_change_permission(self, request, obj=None): return False
    def has_delete_permission(self, request, obj=None): return False
```

- Las 7 clases heredan de `SoloLectura` y solo agregan `list_display`, `search_fields` y `list_filter`.
- Queda ver, buscar y navegar entre entidades relacionadas. Crear, modificar y eliminar quedan apagados.
- Decisión consciente: la pauta da 15 puntos a ese CRUD. Revertirlo son las 3 líneas de arriba.

```bash
python manage.py makemigrations
python manage.py migrate
python manage.py createsuperuser
```

Nota: `AUTH_USER_MODEL` tiene que quedar fijado **antes** de la primera migración, así que estas migraciones se rehicieron al introducir el usuario propio, y la base se recreó. No hay pérdida: los 46 registros se regeneran desde `datos_nuevos/`.

**Verificar**

- `migrate` termina limpio.
- `/admin/` lista las 7 entidades y el buscador responde.
- Desde Vecino se llega a la Delegación por la relación.
- Se ve `cuentas_usuario`, y ninguna `cuentas_perfilusuario`.

**Commit.**

---

## Fase 2 — Datos

El JSON nuevo es el formato de importación. Se construye entero, con los mismos campos que las tablas, y no se parece al de `Abstergo2`.

**`datos_nuevos/`, 7 archivos**

| Archivo | Origen | Contenido |
|---|---|---|
| `delegaciones.json` | transformado | 6 filas |
| `roles.json` | transformado | 6 filas |
| `usuarios.json` | transformado | 6 filas |
| `metas.json` | escrito a mano | ficticias |
| `tipos_atencion.json` | escrito a mano | ficticias |
| `sub_atenciones.json` | escrito a mano | ficticias |
| `vecinos.json` | escrito a mano | ficticias |

**Los tres transformados**

- `delegaciones.json`: `codigo` y `nombre` del origen, más `direccion` y `comuna` agregadas. Se descartan `territorio`, `encargado`, `enfasis` e `imagen`.
- `roles.json`: los 6 roles distintos que trae el origen. `nombre` se saca de `usuarios.json` y `descripcion` se escribe.
- `usuarios.json`: `nombre`, `email`, `rol`, `activo` y `delegacion`. Se descartan `id`, `cargo` y `avatar_color`. `activo` llega hasta `is_active` en el usuario.

Origen exacto: `Abstergo2/apps/delegacion/data/delegaciones.json` (6 filas) y `Abstergo2/apps/usuarios/data/usuarios.json` (6 filas, con los roles ADMIN, COORDINADOR, DELEGADO, FUNCIONARIO, VERIFICADOR y CONSULTA).

`compromisos.json` y `actividades.json` no se leen.

**Los cuatro escritos a mano**

- Con suficientes filas para que cada listado y cada búsqueda tengan algo que mostrar.
- Solo datos ficticios, nunca reales.
- `sub_atenciones.json` referencia el nombre de su tipo de atención.
- `vecinos.json` referencia el código de su delegación, y `metas.json` también.

**Cargar.** Comando en `apps/panel/management/commands/cargar_datos.py`, en orden de dependencia: delegaciones y roles, después usuarios, luego los catálogos, y al final vecinos.

```bash
python manage.py cargar_datos
```

- Escribe con `update_or_create` e informa creados y actualizados.
- Asigna la contraseña de los 6 usuarios con `set_password()`. Sin eso, el login de la Fase 4 no tiene con qué entrar. Si un usuario no trae correo, la contraseña queda inutilizable: ese usuario existe pero no entra.
- Los usuarios se buscan por nombre y apellido, no por correo: un correo nulo no sirve como llave de `update_or_create`.

**Verificar**

- Los 7 archivos no traen ninguna llave que no exista como campo en el modelo.
- Correr `cargar_datos` dos veces seguidas deja los mismos conteos.
- Las 7 tablas quedan con registros.
- Un usuario migrado con correo entra con la contraseña asignada; uno sin correo, no.
- `documentacion/traslado_de_datos.md` queda escrito en esta fase, no después.

**Commit.**

---

## Fase 3 — Front-end

Sin Bootstrap. El armazón sale del framework de laserena.cl más un CSS propio.

**Recursos**

```bash
curl -o static/css/frameworkV1.css https://framework.laserena.cl/css/frameworkV1.css
```

- `frameworkV1.css` son 15 312 bytes en 616 líneas, verificados hoy.
- Trae `.titulo`, `.subtitulo`, `.btn-muni`, `.btn-muni-v2`, `.btn-muni-v3`, `.btn-importante`, la escala `.tx-1` a `.tx-11`, los grises `.gris-0` a `.gris-100` y las variables `--muni-base` y `--bg-muni-*`. Con eso se arma el listado del §0.4.
- No trae grilla, ni iconos, ni `.escudo`, ni `.logo`.
- Aviso: el propio framework espera Bootstrap en cuatro puntos. `.table-hover`, `.table-responsive` y `.accordion-button` son clases de Bootstrap, y `--bs-tooltip-bg` y `--bs-tooltip-color` son variables suyas. Sin Bootstrap esas reglas quedan inertes. Se ignoran y se escriben las tablas propias.
- Los logos, el escudo y las fotos los pone él, en `static/img`. El plan no descarga ninguno.

**`institucional.css`**

- Sobrescribe `--muni-base` a `#C41230`, con `#DB3334` y `#8B1D19` de apoyo.
- El sidebar toma el rojo de la clase `bg-muni` del propio framework, que lee `--muni-base`. El ítem activo usa `--muni-oscuro`, el Rojo Oscuro del manual.
- Escribe lo que el framework no trae: el layout, el sidebar del §0.1, el header del §0.2 y la tabla del patrón "Listado".
- La tipografía la deja el framework: `html, body` con Segoe UI de primera opción. En Linux cae al genérico, que resuelve a Noto Sans.
- Badges de estado Activo e Inactivo, verde y rojo semánticos.
- Es el único lugar donde vive el armazón: un cambio ahí se ve en las 8 pantallas.

**Plantillas**

- `templates/base.html`: sidebar con marca, Inicio y el grupo Mantenedores con los 7 ítems, más header de usuario.
- `templates/inicio.html`: bienvenida simple, el usuario y su rol, y nada más.
- `templates/listado.html`: el patrón del §0.4, reutilizado por los 7 módulos. Trae el armazón, el buscador en tiempo real, el `{% for %}` y la columna de acciones.
- 7 plantillas de columnas, una por módulo, de unas 20 líneas, que heredan de `listado.html`.
- `templates/formulario.html`: un solo formulario, para las 7 altas y las 7 ediciones.
- `templates/confirmar.html`: la confirmación previa al borrado.
- `templates/cuentas/`: las cuatro pantallas de acceso sobre una base común.

**Listados**

- Cada módulo: `ListView` con `template_name` apuntando a `listado.html`.
- El buscador del §0.4 filtra con `get_queryset` sobre `request.GET.get("q")`, contra los campos de `search_fields`.
- Los botones Agregar, Modificar, Eliminar y Buscar están cableados a sus rutas: no son decorativos.

**CRUD funcional**

- Cada uno de los 7 módulos suma `CreateView`, `UpdateView` y `DeleteView` a su `ListView`. Son 28 vistas en total.
- El formulario se genera del modelo con `ModelForm`, sin campos escritos a mano.
- El botón Nuevo abre el alta, el lápiz la edición y el basurero la confirmación de borrado.
- El borrado es real, no lógico: `PROTECT` impide borrar un Rol, una Delegación o un Tipo de Atención que estén en uso, y el error se le muestra al usuario.
- `LoginRequiredMixin` en las 28 vistas.
- URLs por app, montadas con `include()` y con un nombre por operación.

**Iconos**

- Se buscan y se incorporan a mano, uno por uno.
- Van como SVG en `static/img` o en línea dentro de la plantilla.

**Verificar**

- El sidebar tiene Inicio y los 7 mantenedores, y ningún ítem más.
- Inicio muestra el usuario y su rol.
- Los 7 listados traen los registros cargados desde la base de datos.
- El buscador devuelve resultados distintos de la lista completa.
- Crear, editar y eliminar funcionan en los 7 módulos desde el navegador.
- Dar de baja una Delegación que tiene vecinos funciona: sale del listado y los vecinos siguen mostrando su territorio.
- Lo mismo con un Rol y con un Tipo de Atención en uso.
- En los 4 mantenedores sin borrado lógico el borrado es real: la fila desaparece de phpMyAdmin.
- Recargar el JSON con `cargar_datos` restaura lo dado de baja.
- Ninguna plantilla menciona una clase de Bootstrap.
- Sin sesión, cualquier ruta redirige al login.

**Commit.**

---

## Fase 4 — Autenticación

Cuatro pantallas en `apps/cuentas`, siguiendo el mockup §1 a §4:

- **Login:** correo y contraseña contra `auth.User`, con el hash real de Django.
- **Recuperar:** pide el correo y genera un OTP de 6 dígitos, con la fila de 6 casillas del §3.
- **Validar:** compara el código, exige menos de 10 minutos de vigencia y lo marca como usado.
- **Nueva contraseña:** `set_password()` y de vuelta al login.

- El OTP vive en la sesión: con eso ya expira y no se reutiliza.
- El reenvío del §3 lleva su temporizador, con el mismo plazo de 10 minutos.
- Los requisitos del §4 son mínimo 8 caracteres, una mayúscula, una minúscula, un número y un carácter especial. Se configuran en `AUTH_PASSWORD_VALIDATORS`.
- El correo sale del `.env`: consola en desarrollo, SMTP en el EC2.
- `/admin/` tiene su propio superusuario. El login del sistema es otra cuenta, con rol ADMIN.

**Verificar**

- El código aparece en la consola del servidor.
- Sirve una sola vez y a los 10 minutos ya no sirve.
- Una contraseña que no cumple los requisitos es rechazada.

**Commit.**

---

## Fase 5 — Despliegue en EC2

La instancia y la llave ya existen: `ec2-54-172-183-44.compute-1.amazonaws.com` y `~/.ssh/abstergo-key.pem` (verificados). Apache, PHP y `mariadb105-server` vienen del setup inicial. Estos comandos van en la instancia.

```bash
ssh -i ~/.ssh/abstergo-key.pem ec2-user@ec2-54-172-183-44.compute-1.amazonaws.com
sudo dnf install -y mariadb105-devel gcc python3-devel
sudo systemctl enable --now mariadb
sudo mariadb -e "CREATE DATABASE abstergo CHARACTER SET utf8mb4;"
sudo mariadb -e "CREATE USER 'abstergo'@'localhost' IDENTIFIED BY '<clave>'; GRANT ALL PRIVILEGES ON abstergo.* TO 'abstergo'@'localhost'; FLUSH PRIVILEGES;"

git clone https://github.com/lacteada/abstergo.git abstergo && cd abstergo
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python manage.py migrate
python manage.py cargar_datos
python manage.py collectstatic --noinput
```

- Editar el `.env` de la instancia: `DEBUG=False`, `ALLOWED_HOSTS` con el dominio de la instancia, credenciales de MariaDB y SMTP real.
- gunicorn como servicio: unidad en `/etc/systemd/system/abstergo.service`, con `WorkingDirectory` y `ExecStart` apuntando a `venv/bin/gunicorn config.wsgi:application`.
- Apache hace reverse proxy: Django en `/` y phpMyAdmin en `/phpmyadmin`, con `mod_proxy` ya habilitado.
- Restringir el acceso a phpMyAdmin: no dejarlo abierto a internet.

**Verificar**

- La URL de la instancia abre el login.
- Las 7 tablas, sus registros y sus relaciones se ven en phpMyAdmin.
- Los listados del front traen los mismos registros que la base de datos de la instancia.

**Commit.**

---

## Fase 6 — Documentación

Los tres entregables viven en `documentacion/` y se escriben durante el trabajo, no al final.

- `traslado_de_datos.md`: esquema de origen, esquema nuevo, mapeo campo por campo, lo descartado y por qué.
- `prompts.md`: cada prompt usado y la respuesta aplicada. Es la evidencia de IA.
- `documento_tecnico.md`: descripción, arquitectura, base de datos, AWS, GitHub, ORM, phpMyAdmin e IA.

**Qué prueba cada punto de la pauta**

| Punto | Evidencia | Dónde queda |
|---|---|---|
| EC2, 15 pts | capturas de la instancia, la terminal y la app corriendo | documento_tecnico |
| Git, 10 pts | capturas del repositorio, `git log --oneline` y la clonación | documento_tecnico |
| Variables de entorno, 10 pts | `.env.example` y `settings.py` sin credenciales a la vista | documento_tecnico |
| ORM, 20 pts | modelos, migraciones, consultas ORM y las tablas | documento_tecnico |
| Admin, 15 pts | capturas del Admin con las 7 entidades y el buscador | documento_tecnico |
| Front, 20 pts | capturas de Inicio, de los 7 listados y de un alta del front | documento_tecnico |
| IA, 5 pts | `prompts.md` con prompts y respuestas | prompts.md |
| Documento técnico, 5 pts | el PDF final | entrega |

Las consultas ORM no son el Admin. Son el código que lee y escribe la base: los `queryset` de las vistas, `update_or_create` del comando y un `.query` mostrado desde el shell. El Admin es un cliente más del ORM, no la evidencia.

**Evidencia de IA, desde el historial**

- Cada sesión queda en `~/.commandcode/projects/home-lct/<sesión>.jsonl`, con `message.role` y bloques de texto. El `.meta.json` de al lado trae el título, para elegir la sesión correcta.
- El historial ya está en disco: no hay que copiar prompts a mano.
- El script extrae los turnos de `user` y `assistant` y escribe `documentacion/prompts.md`:

```python
import json, sys, pathlib

src = pathlib.Path(sys.argv[1])
out = pathlib.Path("documentacion/prompts.md")

with src.open() as fh, out.open("w") as w:
    for line in fh:
        rec = json.loads(line)
        if rec.get("type") != "message":
            continue
        msg = rec["message"]
        if msg["role"] not in ("user", "assistant"):
            continue
        for block in msg["content"]:
            if block.get("type") == "text":
                w.write(f"## {msg['role']}\n\n{block['text']}\n\n")
```

- Los avisos internos del sistema van en `meta.injected`, fuera de `content`, así que no ensucian el archivo.
- A cada bloque le conviene una línea de "qué se aplicó de esta respuesta", que es lo que pide la pauta.

**Capturas**

- Instancia EC2 y terminal.
- Repositorio, commits y clonación.
- Modelos y migraciones.
- Consultas ORM: los `queryset` de las vistas y un `.query` desde el shell.
- Tablas, registros y relaciones en phpMyAdmin.
- Inicio, los 7 listados y un alta del front.

**Cierre, de Markdown a PDF**

- Abrir `documentacion/documento_tecnico.md` en VSCodium, previsualizar e imprimir a PDF.
- pandoc no está instalado y no hace falta instalarlo.

**Verificar**

- El PDF abre y trae las capturas de las seis evidencias.
- `prompts.md` trae los prompts de todas las sesiones de trabajo, no solo de la última.

**Commit final.**

---

## Checklist de la rúbrica

- EC2 conectado y entorno virtual activo.
- Proyecto clonado desde GitHub.
- Migraciones aplicadas y tablas visibles en phpMyAdmin.
- Relaciones visibles en phpMyAdmin.
- Registros almacenados en las 7 tablas.
- Listados del front leyendo desde el ORM.
- Consultas ORM demostrables.
- Botones Agregar, Modificar, Eliminar y Buscar visibles y funcionando en cada listado.
- Historial de commits y clonación demostrable.
- Documento técnico en PDF con sus capturas.
