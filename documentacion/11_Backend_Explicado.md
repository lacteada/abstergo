# 11 · El backend explicado, de cero a la rúbrica

Documento para entender y para explicar. Primero arma el modelo mental, después recorre
el código por temas, y al final traduce cada sección a la rúbrica de la Evaluación
Sumativa #2 con lo que hay que decir.

No repite a los otros dos documentos:

- `08_Backend.md` describe la arquitectura (qué apps hay y cómo se conectan).
- `10_Guia_Backend.md` recorre los archivos en orden de ejecución.
- Este documento explica los conceptos y los amarra a los 100 puntos.

Todo lo que sigue está verificado contra el código real en `code/ina/backend/abstergo/`.

---

## 1. El modelo mental, primero

Antes de leer una sola línea del proyecto, retén estas cuatro frases:

- Una **clase** en `models.py` **es** una tabla en la base de datos.
- Una **vista** recibe una petición del navegador y devuelve una respuesta.
- Una **plantilla** es HTML con huecos que la vista rellena.
- Un **archivo de migración** es esa clase convertida a SQL, generada sola.

Django es un framework MTV: Modelo, Template, Vista. El modelo guarda los datos, la
plantilla los muestra, la vista conecta a los dos. Si entiendes "un modelo es una
tabla", todo lo demás en este proyecto es una forma de operar esa idea.

**El hilo completo, en una línea:**

> `.env` → `settings.DATABASES` → modelos (clases) → migraciones (crean las tablas) →
> ORM (`objects`, `todos`) → Admin y vistas leen y escriben → `cargar_datos` llena desde JSON.

**La idea más importante del proyecto:** los datos ya no viven en JSON. El JSON solo
sirve para cargar la base una vez. El sistema lee y escribe siempre con el ORM. Si en la
revisión te preguntan "de dónde salen los datos de la tabla", la respuesta es "de
MariaDB, consultada con el ORM de Django".

---

## 2. El esqueleto: qué pasa cuando el navegador pide una página

Ejemplo real: alguien entra a `GET /vecinos/?q=rural`.

1. El navegador manda la petición al servidor.
2. `config/urls.py` no conoce `/vecinos/`, pero tiene `include("apps.ciudadanos.urls")`,
   así que le pasa el resto de la ruta a esa app.
3. `apps/ciudadanos/urls.py` ve `"vecinos/"` y llama a `views.Listado.as_view()`.
4. Pasan los **middleware** de `settings.MIDDLEWARE`: sesión, autenticación, CSRF. Son
   filtros por los que toda petición cruza antes de llegar a la vista.
5. `LoginRequiredMixin` revisa si hay sesión iniciada; si no, redirige al login.
6. `ListadoBase.get_queryset()` consulta la base: trae los vecinos con
   `select_related("territorio")` y, como viene `q=rural`, agrega un filtro.
7. `get_context_data()` arma el "contexto", el diccionario que la plantilla recibe
   (`titulo`, `seccion`, `etiqueta_nueva`, etc.).
8. `listado.html` es el armazón; `ciudadanos/vecinos_lista.html` llena la tabla. Django
   devuelve el HTML final.

Ese recorrido, con otros nombres, es el de las 28 vistas del proyecto.

---

## 3. Mapa del proyecto

```text
abstergo/
├── manage.py                 puerta de entrada de todos los comandos
├── config/
│   ├── settings.py           lee el .env, define apps, base de datos, plantillas
│   ├── urls.py               enlaza admin/ y las 5 apps
│   └── wsgi.py               lo que ejecuta gunicorn en el EC2
├── apps/
│   ├── common/               compartido; NO es una app de Django
│   │   ├── soft_delete.py    el borrado lógico
│   │   ├── vistas_base.py    las vistas genéricas de los 7 mantenedores
│   │   └── admin_base.py     el Admin base: CRUD y borrado lógico
│   ├── organizacion/         Delegacion
│   ├── cuentas/              Rol, Usuario, autenticación
│   ├── catalogos/            Meta, TipoAtencion, SubAtencion
│   ├── ciudadanos/           Vecino
│   └── panel/                Inicio y el comando cargar_datos
├── datos_nuevos/             JSON de origen, uno por entidad
├── templates/                base.html, listado.html, formulario.html y los listados
├── static/                   css, js, img
└── documentacion/            esta guía y las demás
```

**Qué es una "app" en Django.** Una carpeta con `models.py`, `views.py`, `urls.py` y un
`apps.py` que la registra. Django la descubre porque está en `INSTALLED_APPS`.

**Por qué se registran como `apps.cuentas` y no como `cuentas`.** Porque físicamente
viven dentro de la carpeta `apps/`. La ruta completa le dice a Python dónde buscar.

**Por qué `apps/common/` no está en `INSTALLED_APPS`.** No tiene modelos ni migraciones
ni `apps.py`. Es solo un paquete de código compartido: las vistas base, el Admin base y
el borrado lógico. Si lo registraras como app no ganarías nada, porque no aporta tablas.

**Las 5 apps y su papel**

- `organizacion`: las delegaciones municipales, el territorio.
- `cuentas`: roles, usuarios y todo el flujo de autenticación.
- `catalogos`: datos de referencia (metas, tipos y sub tipos de atención).
- `ciudadanos`: los vecinos, la entidad que todo lo demás referencia.
- `panel`: la pantalla de inicio y el comando que carga los datos. Sin modelos propios.

---

## 4. Las 7 entidades (rúbrica: Modelado con ORM, 20 pts)

### Qué es cada tabla y para qué existe

- **Delegacion** (`organizacion`): una oficina municipal. Campos: `codigo` (único),
  `nombre`, `direccion`, `comuna`. Es el "territorio" al que se asignan vecinos, metas y
  usuarios.
- **Rol** (`cuentas`): el perfil de un usuario (por ejemplo ADMIN). Campos: `nombre`
  (único), `descripcion`.
- **Usuario** (`cuentas`): la cuenta del sistema. `email` (único, puede ser nulo), `rol`,
  `delegacion`, `is_active`, y todo lo que aporta `AbstractUser`.
- **Meta** (`catalogos`): un compromiso u objetivo, siempre atado a una `Delegacion`.
- **TipoAtencion** (`catalogos`): categoría de atención. `nombre`, `descripcion`.
- **SubAtencion** (`catalogos`): subcategoría de un `TipoAtencion`.
- **Vecino** (`ciudadanos`): la persona atendida. `nombre`, `rut` (único), `direccion`,
  `telefono`, `territorio` (que es una Delegacion), `tipo_gestion`, `estado`.

### Las relaciones (5 llaves foráneas)

- `Usuario → Rol` (PROTECT)
- `Usuario → Delegacion` (PROTECT)
- `Meta → Delegacion` (PROTECT)
- `SubAtencion → TipoAtencion` (PROTECT)
- `Vecino → Delegacion` (PROTECT)

Palabras que la rúbrica va a poner sobre la mesa y conviene tener claras:

- **PK (llave primaria):** no se escribe en ningún modelo. Django agrega un `id`
  automático para cada tabla (`BigAutoField`).
- **FK (llave foránea):** en el código es `territorio`; en la base es la columna
  `territorio_id`. Guarda el `id` de la fila apuntada, no el objeto.
- **`on_delete=PROTECT`:** si alguien intenta borrar una Delegacion que tenga vecinos,
  la operación se rechaza. Es lo que obliga a inventar el borrado lógico (sección 7).
- **`related_name="vecinos"`:** habilita el camino inverso. Desde una delegación puedes
  escribir `delegacion.vecinos.all()` y obtienes sus vecinos.
- **`null` y `blank`:** `null` es la base (acepta vacío), `blank` es el formulario
  (acepta vacío en pantalla). No significan lo mismo.
- **`verbose_name`:** la etiqueta que ve el usuario. El primer texto entre comillas.
- **`class Meta`:** opciones que no son columnas, como `ordering` (orden por defecto) o
  `verbose_name_plural` (el nombre en el Admin).
- **`abstract = True`:** la clase sirve para heredar y **no** crea tabla. Es lo que pasa
  con `Eliminado` y `BorradoLogico`.

### El caso especial: Usuario

`Usuario` no es el usuario de Django. Es un modelo propio que hereda de `AbstractUser`.
Tres decisiones que conviene poder explicar:

- **No tiene `username`** (`username = None`). La identidad es el `id`, y el correo es un
  dato más, editable sin romper nada.
- **El correo es el campo de acceso** (`USERNAME_FIELD = "email"`). Por eso el login pide
  correo y no nombre de usuario.
- **`objects` sigue siendo un `UserManager`.** Django necesita ese gestor para que
  funcionen `createsuperuser`, `authenticate` y las sesiones. Por eso `Usuario` hereda
  de `Eliminado` y no de `BorradoLogico`.

Como el correo admite nulos, varios usuarios pueden no tener correo sin chocar contra el
índice único. Ese usuario existe en la base, pero no puede iniciar sesión.

`UsuarioManager` reescribe `create_user` y `create_superuser` para que el primer
argumento sea el correo. El de Django exige `username`, que ya no existe.

---

## 5. Las migraciones (rúbrica: Modelado, 20 pts)

**Qué es una migración:** el modelo traducido a SQL. No la escribes tú, la genera Django
a partir de las clases.

**El par de comandos:**

- `makemigrations` mira los modelos y escribe el archivo en `migrations/`.
- `migrate` ejecuta ese archivo contra la base y crea o altera las tablas.

**Qué hay en el proyecto:** cuatro archivos `0001_initial.py`, uno por app con modelos:
`organizacion`, `cuentas`, `catalogos` y `ciudadanos`. La app `panel` no tiene, porque no
tiene modelos.

**Las dependencias, que explican el orden.** Al inicio de cada migración hay una lista
`dependencies`:

- `organizacion` no depende de nada: va primero.
- `cuentas` depende de `auth` (por `AbstractUser`) y de `organizacion` (por la FK a
  Delegacion).
- `catalogos` y `ciudadanos` dependen de `organizacion` (por la FK a Delegacion).

Eso garantiza que `migrate` cree la tabla Delegacion antes de que alguien la referencie.

**Un detalle fino:** la migración de `Usuario` guarda
`managers=[('objects', apps.cuentas.models.UsuarioManager())]`. Es la constancia del
manager propio dentro del archivo.

**Qué mostrar en la verificación cruzada.** La rúbrica exige que modelo, migración,
tabla y phpMyAdmin calcen. En phpMyAdmin deberías poder mostrar estas tablas:

- `organizacion_delegacion`
- `cuentas_rol`, `cuentas_usuario`
- `catalogos_meta`, `catalogos_tipoatencion`, `catalogos_subatencion`
- `ciudadanos_vecino`

El nombre sigue el patrón `app_modelo`. Además existe `django_migrations`, que es la
tabla interna donde Django anota qué migraciones ya aplicó.

---

## 6. El ORM en acción (rúbrica: Modelado y Front End)

**Qué es el ORM:** la capa que te deja consultar la base escribiendo Python en vez de
SQL. En todo el proyecto **no hay una línea de SQL escrita a mano** ni uso de `cursor()`
o `raw()`.

**Los gestores.** Cada modelo tiene un atributo `objects` que es la puerta de entrada a
las consultas:

- `Vecino.objects.all()` trae todos.
- `Delegacion.objects.get(codigo="centro")` trae una sola fila, buscada por código. Si no
  existe, lanza error.
- `Vecino.objects.filter(estado="Activo")` trae las que cumplan.

**`update_or_create`.** Lo usa el comando de carga. Busca por una clave y, si la fila
existe, la actualiza; si no, la crea. Por eso el comando se puede correr dos veces sin
duplicar nada.

**Los operadores que aparecen en el buscador.**

- `icontains` es el `LIKE '%texto%'` de SQL, sin distinguir mayúsculas de minúsculas.
- El doble guion bajo cruza una relación: `territorio__nombre` significa "el nombre de
  la delegación apuntada". El ORM agrega el JOIN solo.
- `Q(...) | Q(...)` arma un OR. Así una sola caja de búsqueda revisa varios campos a la
  vez.

**`select_related`.** Cuando la plantilla recorre una FK fila por fila, Django haría una
consulta extra por cada fila (el problema N+1). `select_related("territorio")` trae todo
con un JOIN en una sola consulta. Por eso cada listado declara `relacionadas`.

**Lo que el ORM genera por debajo.** Esta consulta:

```python
Vecino.objects.filter(territorio__nombre="Centro")
```

produce un SQL con `INNER JOIN` entre `ciudadanos_vecino` y `organizacion_delegacion`.
Ese JOIN es la prueba de que la relación existe y se usa.

**Un detalle que sorprende al profe:** Django no emite `ON DELETE` en la base. El
comportamiento de `PROTECT` lo resuelve el propio Django desde Python. Por eso las claves
foráneas funcionan igual en MariaDB y en SQLite.

---

## 7. El borrado lógico, el concepto que explica todo lo demás

Esta es la pieza que más confunde si se lee suelta, así que va con su historia.

**El problema.** Con `on_delete=PROTECT`, una Delegacion que tenga vecinos no se puede
borrar. Cambiar a cascada borraría a los vecinos, y dejarlo en `SET_NULL` dejaría al
vecino sin territorio. Ninguna de las tres sirve.

**La solución.** No borrar nunca. En vez de eliminar la fila, se le escribe una fecha en
una columna llamada `eliminado`. La fila "desaparece" de la vista pero sigue en la base,
así nadie pierde su referencia.

**Las dos clases abstractas de `apps/common/soft_delete.py`:**

- **`Eliminado`:** aporta el campo `eliminado` y el método `eliminar()`, que escribe la
  fecha en vez de borrar. No crea tabla.
- **`BorradoLogico`:** es `Eliminado` más dos gestores. No crea tabla.

**Los dos gestores, que son el corazón del asunto:**

- **`objects`** (con `ActivosManager`): filtra `eliminado__isnull=True`. Esconde lo dado
  de baja. Es el que usas sin pensar.
- **`todos`** (con `TodosManager`): no filtra nada. Muestra también lo dado de baja.

**Quién usa qué:**

- Las 6 entidades que otras referencian (Delegacion, Rol, Meta, TipoAtencion,
  SubAtencion, Vecino) heredan de `BorradoLogico`, o sea tienen los dos gestores.
- `Usuario` hereda solo de `Eliminado`, porque no puede cambiar su gestor.

**La consecuencia práctica que hay que saber explicar:** un `Vecino.objects.count()`
puede no coincidir con el número de filas que ves en phpMyAdmin. La base tiene más filas
que el ORM, porque el ORM esconde las dadas de baja. No es un error, es el diseño.

**Cómo se conecta con `cargar_datos`.** El comando usa `modelo.todos` y pone
`eliminado = None`. Así, si alguien dio de baja una delegación desde la interfaz, recargar
el JSON la restaura en vez de chocar contra su código único.

**Cómo se conecta con la vista de borrado.** `BorradoBase.form_valid` llama a
`eliminar()` si el modelo tiene ese método, y a `delete()` si no. Como las 7 entidades
heredan de `Eliminado`, en la práctica nunca se borra una fila: siempre se marca.

---

## 8. Django Admin (rúbrica: 15 pts)

**Qué es.** El panel que Django trae hecho, en `/admin/`. Por cada modelo registrado
obtienes pantallas de listar, ver, crear, editar y borrar, sin escribir una vista.

**Cómo se registra un modelo.** Cada `admin.py` usa el decorador:

```python
@admin.register(Vecino)
class VecinoAdmin(AdminBase):
    list_display = ("nombre", "rut", "direccion", "telefono", "territorio",
                    "tipo_gestion", "estado")
    search_fields = ("nombre", "rut", "direccion", "telefono",
                     "territorio__nombre", "tipo_gestion")
    list_filter = ("territorio", "estado")
    autocomplete_fields = ("territorio",)
```

Las cuatro opciones que hay que poder nombrar:

- **`list_display`:** las columnas de la pantalla de listado.
- **`search_fields`:** los campos que revisa la caja de búsqueda. El `__` cruza la FK,
  igual que en el ORM.
- **`list_filter`:** los filtros laterales.
- **`autocomplete_fields`:** convierte un desplegable enorme en un buscador. Requiere que
  el modelo apuntado tenga `search_fields`.

**Las 7 entidades están registradas:** `Delegacion`, `Rol`, `Usuario`, `Meta`,
`TipoAtencion`, `SubAtencion`, `Vecino`. Ninguna queda sin Admin.

**El detalle que hay que saber explicar:** todas heredan de `AdminBase`, que trae el CRUD
completo —alta, edición y borrado— y sobrescribe el borrado para marcar `eliminado` en
vez de emitir un `DELETE`. Al ser una sola base, el comportamiento se escribe una vez y
llega a las 7 entidades.

**Caso propio, `Usuario`.** Es un `AbstractUser` sin `username`, con el correo como
`USERNAME_FIELD`. Se administra con el `UserAdmin` de Django y con formularios que traen
`password1`/`password2`, para cifrar la contraseña al crear o al cambiarla. Como su gestor
no filtra el borrado lógico, el Admin deja fuera los `eliminado`.

---

## 9. El front-end que consume el ORM (rúbrica: 20 pts)

**La arquitectura de las vistas.** Los 7 mantenedores tienen 4 vistas cada uno (listado,
alta, edición, borrado), 28 en total. Todas son vistas genéricas de Django y ninguna
escribe el comportamiento: heredan de `apps/common/vistas_base.py`.

- `ListadoBase` extiende `ListView`.
- `AltaBase` extiende `CreateView`.
- `EdicionBase` extiende `UpdateView`.
- `BorradoBase` extiende `DeleteView`.

**La idea que hay que destacar:** cada `views.py` declara solo sus datos (modelo,
formulario, título, plantilla, nombres de ruta). El comportamiento vive una sola vez en
la base común. Agregar un mantenedor nuevo son cuatro clases cortas.

**Cómo se sirve un listado.** `listado.html` es el armazón (buscador, botones, encabezado
de tabla, paginación). Cada módulo llena `encabezado` y `fila`. Por eso las plantillas se
llaman `ciudadanos/vecinos_lista.html`, `catalogos/metas_lista.html`, etc.

**Los botones que exige la rúbrica.** Agregar, Modificar, Eliminar y Buscar existen
visualmente. Agregar apunta a `url_nueva` (resuelta con `reverse`), y Buscar usa el
parámetro `?q=` del listado. La búsqueda ya funciona de verdad contra el ORM.

**La seguridad de las vistas.** `LoginRequiredMixin` está en todas. Sin sesión iniciada,
cualquier listado redirige al login.

---

## 10. Autenticación

- **Login:** la vista de Django (`LoginView`) con un formulario propio (`FormularioLogin`)
  solo para rotular. El campo se llama `username` por dentro aunque en pantalla diga
  "Correo electrónico", porque así lo espera Django.
- **Logout:** por POST, que es lo que exige Django 5 en adelante.
- **Recuperar contraseña:** código OTP de 6 dígitos, generado con
  `secrets.randbelow(1000000)`.

**Cómo viaja el OTP, que es la parte elegante.** El código vive en la **sesión** del
navegador, no en una tabla. Se guardan `otp_codigo`, `otp_usuario` y `otp_expira`. Vive
ahí porque no necesita persistencia y porque así no se puede reutilizar: al validarlo se
borra de la sesión y se marca `otp_validado`.

**La respuesta al pedir el código es siempre la misma,** exista o no el correo. Así nadie
puede averiguar qué cuentas existen probando direcciones.

**El guardado de la contraseña** usa `set_password`, que hashea con PBKDF2. La contraseña
en claro no se guarda nunca.

**El validador propio** (`apps/cuentas/validators.py`) exige mayúscula, minúscula y un
carácter especial. Está enganchado desde `settings.AUTH_PASSWORD_VALIDATORS`, junto a los
validadores de Django.

---

## 11. Variables de entorno (rúbrica: 10 pts)

La rúbrica exige que nada sensible esté escrito en el código. Se cumple así:

- `settings.py` empieza con `load_dotenv(BASE_DIR / ".env")`, que carga el archivo.
- Un helper `env(nombre, default)` lee cada valor. Hay también `env_bool` y `env_list`
  para los que no son texto.
- `SECRET_KEY`, `DEBUG`, `ALLOWED_HOSTS`, las credenciales de la base y del correo salen
  todas del `.env`.
- `.env` está en `.gitignore`, así que no se sube a GitHub. `.env.example` sí se
  versiona, con las llaves vacías, como plantilla.
- `requirements.txt` trae `python-dotenv`, que es la librería que hace la lectura.

Frase para la revisión: "las credenciales de la base viven en `.env`, que no está en el
repositorio; el código solo conoce el nombre de la variable".

---

## 12. Infraestructura y Git (rúbrica: 15 + 10 pts)

**La puerta de entrada.** `manage.py` le dice a Django dónde están los settings
(`DJANGO_SETTINGS_MODULE = "config.settings"`) y le pasa los argumentos. Todos los
comandos entran por ahí: `runserver`, `migrate`, `cargar_datos`, `createsuperuser`.

**Lo de producción.** `config/wsgi.py` exporta una variable `application`. Eso es lo que
ejecuta el servidor en el EC2: `gunicorn config.wsgi:application`.

**El `requirements.txt`** trae Django, `python-dotenv`, `gunicorn`, `asgiref` y
`sqlparse`.

**El tropiezo que hay que tener presente.** `requirements.txt` **no** incluye
`mysqlclient`, que es el driver de MySQL/MariaDB. Sin ese driver, el `ENGINE` mysql no
conecta y `runserver` aborta con `Error loading MySQLdb module`. Se instala aparte, después
de tener MariaDB y sus librerías de desarrollo:

```bash
pip install mysqlclient
```

**La secuencia del despliegue**, que la rúbrica evalúa en vivo:

```bash
git clone URL_DEL_REPOSITORIO
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
pip install mysqlclient
cp .env.example .env        # completar credenciales
python manage.py migrate
python manage.py cargar_datos
python manage.py runserver  # o gunicorn en producción
```

---

## 13. Documentación y evidencia de IA (rúbrica: 5 + 5 pts)

- **Documentación técnica:** `documento_tecnico.md` (se exporta a PDF). Debe incluir
  descripción, arquitectura, y capturas de AWS, GitHub, la base y phpMyAdmin.
- **Evidencia de IA:** `prompts.md`. La rúbrica pide prompts, respuestas obtenidas y
  cómo se aplicaron al proyecto.
- **Mapeo de datos:** `traslado_de_datos.md` explica del JSON de origen a las tablas.

---

## 14. Chuleta para la revisión

Preguntas probables y respuesta corta.

- **¿Dónde está la base de datos configurada?**
  En `config/settings.py`, en `DATABASES`, con los valores leídos del `.env`.
- **¿Qué son las migraciones?**
  El modelo traducido a SQL. Las genera `makemigrations` y las aplica `migrate`.
- **¿Cuántas tablas hay?**
  Siete propias, más las internas de Django (`django_migrations`, `django_session`,
  `auth_*`, `django_content_type`).
- **¿Por qué el borrado no borra?**
  Porque las FK usan `PROTECT`. Se marca la fecha en `eliminado` para no perder las
  referencias. Es el borrado lógico.
- **¿Por qué los conteos del ORM no calzan con phpMyAdmin?**
  Porque `objects` esconde los registros con `eliminado` distinto de nulo. La base tiene
  más filas que el ORM.
- **¿Por qué el usuario no tiene nombre de usuario?**
  Porque el correo es el campo de acceso (`USERNAME_FIELD`), y la identidad es el `id`.
- **¿De dónde salen los datos que se ven?**
  Del ORM, siempre. El JSON de `datos_nuevos/` ya solo se usa para cargar una vez.
- **¿Cómo se evita el N+1?**
  Con `select_related`, que trae las FK en la misma consulta mediante JOIN.
- **¿Cómo es idempotente el cargar_datos?**
  Con `update_or_create`: busca por una clave y actualiza si existe, crea si no.

**El hilo, otra vez, para cerrar:** `.env → settings.DATABASES → modelos → migraciones →
ORM → Admin y vistas → cargar_datos`.

---

## 15. Inconsistencias detectadas en el código y en los documentos

Cosas que encontré al verificar el código contra los documentos. Conviene decidir una
versión única antes de la entrega.

- **`requirements.txt` no incluye `mysqlclient`.** El README lo instala aparte en un paso
  propio, así que funciona, pero un `pip install -r requirements.txt` a secas no levanta.
- **La versión de Django.** `requirements.txt` fija `Django==6.1.1`, mientras el
  comentario de `settings.py` dice que `MAILERS` reemplaza a `EMAIL_BACKEND` "desde Django
  6.0" y `documento_tecnico.md` dice 6.1. Hay que unificar el número.
- **`08_Backend.md` dice que en cuatro entidades el borrado es real.** El código no hace
  eso: las 7 heredan de `Eliminado`, así que `BorradoBase` siempre llama a `eliminar()`.
  La frase correcta es "el borrado es lógico en las 7 entidades".
- **`10_Guia_Backend.md` describe el borrado lógico como excepción de algunas tablas.**
  En el código es la regla general, y `Usuario` es la única con matiz (hereda de
  `Eliminado` sin los gestores).
