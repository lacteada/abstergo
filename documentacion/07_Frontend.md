# 07 · Front-end — guía de estudio

Material para estudiar cómo está armado y cómo funciona el front-end.
Amplía el §6 de `documento_tecnico.md` y es la contraparte práctica de
`00_Analisis_Frontend.md` (que analiza el portal original, no este sistema).

## 1. En una frase

Plantillas Django renderizadas en el servidor, con dos hojas de estilo (el
framework institucional y el armazón propio) y un único JS para la búsqueda en
vivo. Sin SPA, sin Bootstrap, sin framework de CSS.

## 2. Mapa de archivos

```text
templates/
├── base.html              armazón: sidebar + header (usuario) + contenido
├── listado.html           patrón de listado; lo extienden los 7 módulos
├── formulario.html        alta y edición; lo comparten los 7
├── confirmar.html         confirmación antes de dar de baja
├── inicio.html            pantalla de Inicio
├── cuentas/
│   ├── base_auth.html     armazón de las pantallas de acceso
│   ├── login.html
│   ├── recuperar.html
│   ├── validar.html
│   └── nueva_password.html
├── organizacion/delegaciones_lista.html
├── cuentas/roles_lista.html
├── cuentas/usuarios_lista.html
├── catalogos/metas_lista.html
├── catalogos/tipos_lista.html
├── catalogos/subatenciones_lista.html
└── ciudadanos/vecinos_lista.html

static/
├── css/frameworkV1.css    institucional: tokens, tipografía, botones, tabla
├── css/institucional.css  armazón propio: grilla, sidebar, header, tabla
├── js/busqueda.js         búsqueda en vivo de los listados
└── img/logolaserena.png
```

## 3. Herencia de plantillas

Django permite que una plantilla **extienda** otra y rellene sus bloques
(`{% block %}`). Es el mecanismo central de este front.

- `base.html` = armazón. Define los bloques `titulo` y `contenido`.
- `listado.html` extiende `base.html` y define el patrón de listado, con dos
  bloques para que cada módulo los llene: `encabezado` (los `<th>`) y `fila`
  (los `<td>`).
- Cada módulo extiende `listado.html` y llena esos dos bloques. Nada más.

Ejemplo real (`templates/catalogos/tipos_lista.html`, completo):

```django
{% extends "listado.html" %}

{% block encabezado %}
  <th>#</th>
  <th>Nombre</th>
  <th>Descripción</th>
  <th>Acciones</th>
{% endblock %}

{% block fila %}
  <td>{{ fila.id }}</td>
  <td>{{ fila.nombre }}</td>
  <td>{{ fila.descripcion }}</td>
  <td class="acciones">
    <a class="accion" href="{% url 'catalogos:tipos_editar' fila.pk %}">Editar</a>
    <a class="accion peligro" href="{% url 'catalogos:tipos_eliminar' fila.pk %}">Eliminar</a>
  </td>
{% endblock %}
```

Por qué importa: los 7 listados comparten una sola plantilla de armazón. Un
cambio en `listado.html` (por ejemplo el botón `+ Nuevo`) se ve en los 7 de una
vez, y no hay que tocar cada módulo.

## 4. El armazón: `base.html`

Estructura:

```text
<body>
  <div class="app">
    <aside class="sidebar bg-muni">     sidebar con Inicio y Mantenedores
    <div class="contenido">
      <header class="header">           barra superior con el usuario
      <main class="main">               {% block contenido %} va acá
```

Puntos:

- `.app` es un flex que pone el sidebar y el contenido uno al lado del otro.
  `flex-wrap: nowrap` evita que el contenido se vaya abajo al angostar o hacer
  zoom.
- El sidebar sale del `bg-muni` (rojo institucional) y marca la sección activa
  con `{% if seccion == '...' %}activo{% endif %}`. La variable `seccion` la
  manda la vista de cada módulo.
- El bloque `titulo` cambia el `<title>` de la pestaña.

## 5. El patrón de listado: `listado.html`

Es el corazón del front. Estructura actual:

```django
{% extends "base.html" %}
{% load static %}

{% block contenido %}

  <div class="cabecera">
    <h1 class="titulo">{{ titulo }}</h1>
    <a class="btn-muni" href="{{ url_nueva }}">+ {{ etiqueta_nueva }}</a>
  </div>
  {% if subtitulo %}<p class="subtitulo">{{ subtitulo }}</p>{% endif %}

  <div class="barra">
    <form class="buscador" method="get">
      <span class="buscador-campo">
        <input type="search" name="q" value="{{ request.GET.q|default:'' }}"
               placeholder="Buscar..." autocomplete="off"
               data-busqueda data-url="{% url url_listado %}">
        <svg class="buscador-lupa" viewBox="0 0 24 24" ...>{{ /* lupa */ }}</svg>
      </span>
    </form>
  </div>

  <div class="tabla-envoltura">
    <table class="tabla">
      <thead>
        <tr>{% block encabezado %}{% endblock %}</tr>
      </thead>
      <tbody data-filas>
        {% for fila in object_list %}
          <tr>{% block fila %}{% endblock %}</tr>
        {% empty %}
          <tr><td colspan="20" class="vacio">Sin registros.</td></tr>
        {% endfor %}
      </tbody>
    </table>
  </div>

  <p class="pie" data-pie>{{ object_list|length }} registro{{ object_list|length|pluralize }}.</p>

  <script src="{% static 'js/busqueda.js' %}"></script>

{% endblock %}
```

Las cuatro variables que la vista le entrega:

- `titulo` : encabezado y `<title>`.
- `subtitulo` : línea bajo el título (opcional).
- `etiqueta_nueva` : texto del botón, sin el "más" (por ejemplo `Nuevo usuario`).
- `url_nueva` / `url_listado` : rutas por nombre, resueltas con `{% url %}`.

Los dos ganchos que usa el JS son `data-filas` (el `<tbody>`) y `data-pie` (el
contador); `data-busqueda` y `data-url` marcan y configuran el input.

## 6. Las dos hojas de estilo

### Orden de carga

1. `frameworkV1.css`
2. `institucional.css`

Se cargan en ese orden y, a igual especificidad, gana la última. Por eso
`institucional.css` puede corregir reglas del framework.

### `frameworkV1.css` (externo, del portal)

Aporta: variables (`--muni-base`, `--bg-muni-*`, grises `--gris-0`..`--gris-100`,
escala de texto `--tx-1`..`--tx-11`), tipografía, `.titulo`/`.subtitulo`,
botones `.btn-muni*` y la tabla base.

### `institucional.css` (propio)

Aporta lo que el framework no trae: `.app`, sidebar, header, `.main`,
`.cabecera`, `.barra`, `.buscador*`, `.tabla-envoltura`, `.tabla`, los badges
`.estado`, los formularios y las pantallas de acceso. Su encabezado lo dice:
"Solo lo que frameworkV1.css no trae".

Regla práctica para orientarse:

- "cómo se ve un botón o un texto" → `frameworkV1.css`.
- "cómo se distribuye la pantalla" → `institucional.css`.

## 7. La tabla y el bug del zoom (caso de estudio)

Síntoma: al hacer zoom en el navegador, la tabla se desarmaba en bloques y el
encabezado desaparecía.

Causa: `frameworkV1.css` traía un media query que convertía **cualquier**
`table` en tarjetas:

```css
@media screen and (min-width: 350px) and (max-width: 768px) {
  table tr { display: block; }
  table td { display: block; }
  table thead { display: none; }
  table td:before { content: attr(data-cell); }
}
```

El zoom reduce el ancho de viewport **en px CSS**. Con la ventana a más de
768px, al hacer zoom (por ejemplo 200%) el ancho cae por debajo de 768, el
media query se dispara y la tabla pasa a `display: block`.

Fix aplicado: acotar esas reglas a `.table-responsive table ...`. Así la
conversión a tarjetas es opt-in (sólo si la tabla va dentro de
`.table-responsive`) y la tabla propia conserva su estructura a cualquier zoom.

Y para que no se rompa si el contenido no cabe, `institucional.css` aporta:

```css
.tabla-envoltura { overflow-x: auto; max-width: 100%; }
.tabla th, .tabla td { white-space: nowrap; }
```

Es decir: no se envuelve en varias líneas; se desplaza en horizontal.

## 8. El buscador en vivo: `static/js/busqueda.js`

Sin recargar la página. Pide la misma URL del listado con `?q=`, se queda con
las filas de la respuesta y las cambia en la tabla.

```js
function iniciarBusqueda() {
  const entrada = document.querySelector("[data-busqueda]");
  if (!entrada) return;
  const filas = document.querySelector("[data-filas]");
  const pie = document.querySelector("[data-pie]");
  let temporizador = null;

  async function actualizar() {
    const destino =
      entrada.dataset.url + "?q=" + encodeURIComponent(entrada.value.trim());
    const respuesta = await fetch(destino);
    if (!respuesta.ok) return;
    const documento = new DOMParser().parseFromString(
      await respuesta.text(), "text/html");
    const nuevasFilas = documento.querySelector("[data-filas]");
    if (nuevasFilas) filas.innerHTML = nuevasFilas.innerHTML;
    const nuevoPie = documento.querySelector("[data-pie]");
    if (nuevoPie) pie.innerHTML = nuevoPie.innerHTML;
  }

  entrada.addEventListener("input", () => {
    clearTimeout(temporizador);
    temporizador = setTimeout(actualizar, 250);   // espera 250 ms antes de pedir
  });
}
```

Ideas para estudiar:

- El `setTimeout` con `clearTimeout` es un patrón "debounce": no dispara una
  petición por tecla, sólo cuando el usuario deja de escribir 250 ms.
- No hay endpoint nuevo: se reusa la misma vista del listado, que ya filtra por
  `?q=`. El JS sólo se queda con un pedazo del HTML.
- El `<form method="get">` sigue ahí aunque no haya botón: sin JavaScript, el
  Enter en el input hace la carga completa de siempre.

## 9. El botón "+ Nuevo [Entidad]"

- La etiqueta la pone la **vista**, no la plantilla: es el atributo
  `etiqueta_nueva` en `apps/common/vistas_base.py`.
- Cada listado declara la suya: `"Nuevo usuario"`, `"Nueva delegación"`,
  `"Nueva meta"`, `"Nuevo vecino"`, etc.
- La plantilla sólo la pinta: `>+ {{ etiqueta_nueva }}<`.
- Estilo `.btn-muni` (framework): `display: inline-block`, `padding: 10px 18px`,
  `font-weight: bold`, `text-decoration: none`, `border-radius: 6px`.

Por qué la etiqueta va en la vista: la plantilla es una sola para los 7
listados; el texto cambia por entidad. Ponerlo en el HTML obligaría a duplicar
la plantilla o a llenar condicionales.

## 10. El usuario del header (dropdown sin JavaScript)

`<details>`/`<summary>` abre y cierra solo, sin JS. El logout va por POST con
`{% csrf_token %}` (desde Django 5 el logout no acepta GET).

```django
<details class="usuario">
  <summary class="usuario-resumen">
    <span class="avatar"><svg .../></span>          icono de persona
    <span class="usuario-textos">
      <span class="usuario-nombre">{{ user.get_full_name|default:user.username }}</span>
      <span class="usuario-rol">{{ user.perfil.rol|default:"sin rol" }}</span>
    </span>
    <span class="usuario-flecha"><svg .../></span>   chevron del desplegable
  </summary>
  <div class="usuario-menu">
    <form method="post" action="{% url 'cuentas:logout' %}">
      {% csrf_token %}
      <button type="submit" class="usuario-salir">Cerrar sesión</button>
    </form>
  </div>
</details>
```

Detalles:

- `user.perfil` es una relación `OneToOne`; si no existiera, el template
  devuelve vacío (Django silencia `ObjectDoesNotExist`) y se muestra "sin rol".
- El menú se posiciona absoluto (_absolute_) bajo el resumen
  (`.usuario-menu { position: absolute; right: 0; top: calc(100% + 8px) }`).

## 11. Formularios y confirmación

- `formulario.html` sirve para alta y edición. Recorre `{% for campo in form %}`,
  pinta `label`, el campo, `help_text` y errores, y cierra con Guardar/Cancelar.
- `confirmar.html` pregunta antes de dar de baja y manda el POST de borrado.
- Ambos comparten `.formulario`, `.campo`, `.botonera` y el botón `.btn-muni`.

El formulario de Django (`{{ campo }}`) ya trae el `<input>`/`<select>` con su
tipo y sus validaciones HTML; la plantilla no repite nada.

## 12. Autenticación (pantallas)

`templates/cuentas/base_auth.html` es el armazón de las cuatro pantallas
(login, recuperar, validar, nueva contraseña). Comparten `.auth`, `.auth-tarjeta`
y el botón `.auth-boton` (ancho completo). El back-end de este flujo está en
`08_Backend.md` §13.

## 13. Cómo levantar esto en local

El proyecto está configurado a MariaDB. Para verlo sin MariaDB se usó un SQLite
temporal en el scratchpad del agente (`settings_sqlite.py` + `abstergo.sqlite3`),
que **no** está en el repo. El detalle y el comando están en `08_Backend.md` §15.

## 14. Checklist de estudio

- [ ] Sé dibujar la herencia: `base.html` → `listado.html` → `<modulo>_lista.html`.
- [ ] Sé qué variable llena el botón Nuevo y de dónde sale.
- [ ] Sé por qué el zoom desarmaba la tabla y cómo se arregló.
- [ ] Sé cómo el buscador cambia la tabla sin recargar.
- [ ] Sé por qué dos CSS y en qué orden se cargan.
