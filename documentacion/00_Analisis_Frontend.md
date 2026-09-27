# Diseño front-end — Portal Municipal de La Serena

Análisis técnico del front-end de `https://laserena.cl/`.
Fecha del análisis: 2026-09-24.

Alcance: arquitectura de la aplicación, stack y dependencias, sistema de diseño (CSS propio), rutas, datos que consume, SEO/PWA y hallazgos. Todo lo afirmado abajo proviene de los archivos listados en la sección **Evidencia**.

---

## 1. Resumen

- El portal es una **SPA de React 18.3.1** compilada con **Vite**. El HTML del servidor solo trae `<div id="root"></div>`; todo el contenido lo pinta JavaScript en el navegador.
- El diseño **no** usa un tema de React. Se apoya en **Bootstrap 5.3.3 por CDN** más un **CSS propio de la municipalidad** (`frameworkV1.css`), servido desde el subdominio `framework.laserena.cl`.
- Los datos vienen de una **API REST** en `apis.munilaserena.cl` (Laravel), protegida por `Origin`/`Referer`.
- No hay code-splitting: la app entera es **un solo bundle de ~309 KB** (`index-DklO5CaO.js`).

---

## 2. Stack técnico

- **Framework:** React 18.3.1 (`createRoot`, `StrictMode`, `Suspense`).
- **Enrutado:** `react-router-dom` (componentes `Routes`/`Route`; se usó `BrowserRouter`, no el data router, aunque el bundle incluye los dos).
- **HTTP:** `axios`.
- **UI base:** Bootstrap 5.3.3 (CSS y JS bundle, vía jsDelivr con `integrity`) + **Bootstrap Icons 1.11.3**.
- **Mapas:** Leaflet 1.9.4 (CSS y JS desde cdnjs).
- **Build:** Vite (assets con hash, polyfill `modulepreload`, sin chunks por ruta).
- **Analítica:** Google Analytics 4 con **Consent Mode**, ID `G-VS9Y3TBVYC`.
- **Sin** jQuery, Vue, Angular, Svelte, Next/Nuxt ni CMS (WordPress/Sanity/Strapi) en el portal.
- **Sin webfonts:** usa la pila del sistema `'Segoe UI', Tahoma, Geneva, Verdana, sans-serif`.

Versión de React y presencia de librerías verificadas por firmas dentro del bundle (ver sección 12).

---

## 3. Arquitectura de despliegue

Tres hosts con roles distintos:

- **`laserena.cl`** — Apache. Sirve `index.html` y los assets del build (`/assets/index-*.js`, `/assets/index-*.css`).
- **`framework.laserena.cl`** — repositorio central de recursos compartidos: `css/frameworkV1.css`, `js/frameworkV1.js`, `img/*` (escudos, logos, favicon) y `templates/*.html` (footer y barra de transparencia). Responde con `Access-Control-Allow-Origin: *`. Además aloja su **propia** SPA ("Framework", con jQuery + DataTables), separada del portal.
- **`apis.munilaserena.cl`** — API del portal (`/api-portal`) y almacenamiento de imágenes (`/storage/...`). Es un backend Laravel (las páginas de error lo delatan). Existe también `apisdesa.munilaserena.cl/api-formularios/tramites` (entorno de desarrollo referenciado en el código).

Subdominios relacionados que aparecen enlazados: `panoramas.laserena.cl`, `lineadirecta.laserena.cl`, `mantencion.laserena.cl`.

**Hallazgo de configuración:** el servidor devuelve `index.html` para rutas inexistentes. Por eso `robots.txt`, `sitemap.xml` y `site.webmanifest` responden 200 con el HTML del portal (mismo tamaño, 5568 bytes) en vez de su contenido real. En la práctica: **no hay robots.txt, no hay sitemap.xml y el manifest de PWA está roto**.

---

## 4. Sistema de diseño (`frameworkV1.css`)

Archivo propio de 15 KB, con cabecera de autoría: Alejandro Julio Ulloa, Sección de Ingeniería y Desarrollo, 25 de septiembre de 2024. Es la fuente de la identidad visual.

### 4.1 Color

- **Rojo institucional:** `--muni-base: #AD0000`.
- **Rojos claros (a1→a5):** `#f9dcdc`, `#f2b5b5`, `#e08080`, `#cc6666`, `#b33d3d`.
- **Rojos oscuros (b1→b5):** `#7a0000`, `#660000`, `#4d0000`, `#330000`, `#1a0000`.
- **Naranjas (v1→v4):** `#b33d00`, `#cc6600`, `#e08000`, `#f2b500`.
- **Escala de grises (gris-0→gris-100):** de `#fff` a `#000` en pasos de 10%.

Aparecen **dos rojos distintos** para la marca: `#AD0000` en el CSS y `#920000` en el `<meta name="theme-color">` y en el SVG `mask-icon`. Inconsistencia real, no un error de lectura.

### 4.2 Tipografía

- Pila del sistema, sin fuentes descargadas.
- Escala propia `--tx-1` … `--tx-11` que va de `0.7em` a `2.5em`.
- Clases de tamaño `.tx-1` … `.tx-11` aplicables a cualquier elemento.
- Encabezados de sección con `.titulo` (fuente grande en negrita, barra roja a la izquierda de 10 px) y `.subtitulo` (barra gris de 7 px). Ambos con tamaños por breakpoint.

### 4.3 Utilidades y componentes

- **Fondos:** `.bg-muni`, `.bg-muni-a1..a5`, `.bg-muni-b1..b5`, `.bg-muni-v1..v4`, `.bg-gris-10..100`.
- **Botones:** `.btn-muni` (rojo base → hover naranja), `.btn-muni-v2`, `.btn-muni-v3`, y `.btn-importante` con animación de pulso.
- **Animaciones de aviso:** `.bg-importante-1/2/3` (parpadeo entre dos colores).
- **Listas:** `.ulMuni` (viñeta roja custom), `ol.olNum` (decimal), `ol.olLet` (letras).
- **Tablas:** borde, hover de fila y versión responsive que convierte filas en tarjetas usando `data-cell` como etiqueta.
- **Paginación DataTables** estilizada (botones redondos, estados current/previous/next) y flechas de ordenamiento por contenido `::after`.
- **Scrollbar** de página personalizado (color `--bg-muni-b1`).
- **Overrides de Bootstrap:** acordeón (`.accordion-button` rojo), tooltips (`.tooltip-danger`, `.tooltip-success`, `.tooltip-bg-muni-v3`).

### 4.4 Breakpoints

Usa los de Bootstrap 5.3 (576 / 768 / 992 / 1200 / 1400) y añade puntos propios en 360, 389, 425, 480, 768, 1024, 1200 y 1400 px para `.titulo`, `.subtitulo`, `.escudo`, `.logo` y las tablas.

---

## 5. Estilos propios del portal (`index-Db2lHjC1.css`)

Encima del framework, el portal define:

- **Primera línea:** `@import "https://framework.laserena.cl/css/frameworkV1.css"`. El diseño depende de un recurso externo cargado por `@import` (bloquea render y acopla el portal a otro subdominio).
- **Header/navbar:** `.nav-link` en blanco con hover amarillo `#fffb00`; estado activo con fondo `#6d0101` y borde redondeado, con transición de 1 s.
- **Logos:** `.escudo` (40 px) y `.logo` (140–160 px) con anchos por breakpoint.
- **Carrusel de portada:** controles prev/next alineados abajo, información superpuesta (`#info-carrusel` en `top:50%`/`right:10%`, ancho 40%), título en amarillo, y miniaturas (`.carrusel-thumbs`, `.thumb-item`) con `backdrop-filter: blur(4px)`.
- **Clases utilitarias del home:** `.carruselHomePortal`, `.carruselPortal`.

---

## 6. Diseño visual y layout

### 6.1 Estética general

- Estilo institucional sobrio: fondo claro, bloques rojos y tipografía del sistema (sin webfonts ni ilustraciones propias).
- Jerarquía resuelta por **color y barras laterales** (`.titulo`, `.subtitulo`) más que por tamaño de fuente.
- Grilla de 12 columnas de Bootstrap, con contenedores centrados (`container` / `container-fluid`).
- Microinteracciones: tarjetas que cambian al hover, botones que se elevan, carrusel y animaciones de aviso parpadeantes.

### 6.2 Portada — orden de secciones

Reconstruido desde el componente de portada del bundle:

1. Barra superior de transparencia y redes sociales (grupo de botones con iconos Facebook, Instagram, YouTube, X, TikTok).
2. Navbar roja fija (`navbar-expand-lg bg-muni sticky-top`) con logo horizontal y menú dinámico.
3. Carrusel principal de banners, con overlay de texto y miniaturas.
4. Bloque de trámites, con modal por trámite.
5. Noticias, en tarjetas grandes.
6. Servicios municipales, en tarjetas con modal.
7. Buscador y botón "Consulta por Whatsapp IA".
8. "Sitios municipales", en grilla de botones.
9. "Banners de interés comunal", en grilla de imágenes.
10. Barra de accesibilidad flotante y paginación.
11. Breadcrumb.

### 6.3 Componentes visuales

**Tarjeta de noticia** (`.blog-card.spring-fever`):

- 550 × 400 px, imagen de fondo a pantalla completa, texto blanco y sombra proyectada.
- Dos capas encima de la imagen: velo azulado `#40545e80` y degradado oscuro hacia la base.
- Título sobre la imagen y una línea amarilla `#ffae00` que se ensancha al hover.
- Al hover aparecen la descripción y el botón "Leer noticia", y la sombra se intensifica.
- Pie con la fecha (`utility-info` + icono de calendario).
- En móvil el botón se oculta, el texto se centra y el alto baja a 300 px.

**Carrusel de portada:** panel `#info-carrusel` superpuesto (centrado vertical, al 10% de la derecha, 40% de ancho), título amarillo y cuerpo blanco; miniaturas con desenfoque; controles prev/next alineados a la base.

**Botones de sitio** (`.btn-sitios`): fondo naranja `--bg-muni-v1`, 80 px de alto, borde blanco y transición de 1 s.

**Banners** (`.banners`): fondo gris claro, borde blanco y 10 px de padding, con transición al hover.

**Servicios** (`.btnServicio`): borde inferior naranja que crece al hover, con elevación y resplandor rojo.

**Breadcrumb:** negro con borde blanco y esquinas redondeadas.

### 6.4 Barra de accesibilidad (rasgo propio destacado)

- Fija en la base de la ventana, fondo negro, `z-index: 1000`; en escritorio compacta a la derecha y en móvil ocupa el ancho completo.
- Botones: **leer en voz alta** (reproducir/pausar), **aumentar** y **reducir** el tamaño del texto, **restablecer** y **alternar alto contraste**.
- El zoom aplica entre 12 px y 24 px sobre los elementos marcados con la clase `.contAccesible`.
- El contraste agrega la clase `high-contrast` al `body`: fondo negro, texto blanco, logo invertido y en escala de grises, e imágenes en gris de alto contraste.
- La lectura por voz usa `speechSynthesis` del navegador, por lo que requiere una interacción previa del usuario (bloqueo por autoplay).

### 6.5 Layout responsive

- Grilla de Bootstrap, con ajustes propios en 360, 389, 425, 480, 768, 1024, 1200 y 1400 px.
- Las tablas de datos se convierten en tarjetas apiladas por debajo de 768 px.
- La tarjeta de noticia reposiciona el texto y reduce su alto en los cortes de 768, 576 y 380 px.

## 7. Componentes de interfaz (desde el bundle)

- **Barra superior:** navbar Bootstrap con `navbar-toggler` y menú colapsable `#navbarSupportedContents`. Construido dinámicamente desde el menú de la API, con navegación anidada y colapso automático al hacer clic (usa `window.bootstrap.Collapse`).
- **Carrusel principal:** componente sobre el carousel de Bootstrap, alimentado por `carruselPortal`.
- **Trámites:** grilla de botones generada desde `tramitesPortal`; cada botón usa su `icono_tramite` (Bootstrap Icons), su `color_tramite` (p. ej. `bg-muni-v3`) y abre un **modal** por trámite (`Modal_<id>`).
- **Noticias:** tarjetas (`card`) con badges por tipo: `noticia` → `bg-light`, `programa` → `bg-success`, `subsidio` → `bg-primary`, otros → `bg-danger`.
- **Otros:** acordeones (subsidios/programas), tablas (juzgados, concejo), mapas Leaflet (delegaciones), modal de correo de contacto.
- **Funciones destacadas:** buscador (`/buscar` con "Buscar trámite por nombre o descripción…"), **consulta por WhatsApp con IA**, y **lectura por voz (TTS)** de contenidos — con manejo de bloqueo por autoplay.
- **Consentimiento de cookies:** banner "Cookies, Apreciamos tu privacidad" con Aceptar todas / Rechazar no esenciales / Configurar, y categorías Necesarias / Analítica / Marketing y redes sociales.

---

## 8. Rutas de la aplicación

Definidas con `react-router` en el bundle:

- `/` — Portada.
- `/noticias` — Listado de noticias.
- `/noticia/:id_noticias` — Detalle de noticia.
- `/buscar` — Resultados de búsqueda.
- `/el-municipio` — El Municipio.
- `/concejo-municipal` — Concejo Municipal.
- `/Delegaciones` — Delegaciones municipales (nota: con mayúscula).
- `/juzgados` — Juzgados de policía local.
- `/lineaDirecta` — Línea Directa.
- `/organigrama/:slug` — Organigrama.
- `/subsidio/:slug` y `/:parent/subsidios` — Subsidios.
- `/:parent/programas` — Programas municipales.
- `/contenido/:slug`, `/conocenos/:slug`, `/:parent/:slug`, `/:parent/:child` — Contenido genérico.
- `/template` — Página de pruebas de plantillas.
- `tramitesMunicipales` — Trámites (definida **sin barra inicial**, ruta relativa).

Las rutas de contenido se resuelven contra el menú de la API, que **genera el slug** a partir del nombre (normaliza acentos, `&`→`y`, minúsculas, guiones).

---

## 9. Datos que consume (API)

Base: `https://apis.munilaserena.cl/api-portal`.

- `GET /menus` — árbol de navegación (17 ítems, con jerarquía y contenido embebido).
- `GET /carruselPortal` — 13 banners (imagen, enlace, vigencia, orden).
- `GET /tramitesPortal` — 6 trámites (nombre, icono, color, URL, observaciones).
- `GET /serviciosPortal`, `GET /sitios`, `GET /banners`, `GET /noticias`.
- `GET /noticia/:id`, `GET /municipio` (+ `/municipio/slug`), `GET /programas`, `GET /contenidos`, `GET /subsidiosPortal`, `GET /organigrama`, `GET /concejoComunal`, `GET /delegaciones`.
- `POST /enviarCorreo` — formulario de contacto.

Notas:

- Las imágenes se sirven desde `apis.munilaserena.cl/storage/` (`carrusel/`, `banners/`, `concejales/`, `contenido/`).
- La API **rechaza** peticiones sin `Origin`/`Referer` autorizados ("Esta API solo puede ser consumida desde navegadores con dominios autorizados"), y devuelve **429 Too Many Requests** ante ráfagas.
- Hay endpoints de formularios en `apisdesa.munilaserena.cl/api-formularios/tramites`.

---

## 10. Plantillas compartidas y SEO/PWA

### 10.1 Plantillas (`framework.laserena.cl/templates/`)

- `footer.html` — pie de 3 columnas (marca, transparencia, contacto) sobre `bg-gris-90`, con enlaces a Portal de Transparencia, Ley del Lobby, redes sociales y datos de contacto. Se incrusta como **iframe** y se autoajusta: mide su altura y la envía al padre con `postMessage({type:'iframeHeight'})`, además de reportar presencia con un pixel `1x1.gif`.
- `transparencia.html` — barra `bg-black` con accesos a trámites, transparencia, lobby y fono, más botones de redes sociales.
- El SPA las carga en iframes; de ahí los mensajes de error "No se pudo cargar el pie de página" y "No se pudo cargar la barra de transparencia".

### 10.2 SEO

Bien cubierto en el `<head>`: `title`, `description`, `canonical`, `robots`, Open Graph, Twitter Card, `hreflang` (`es-cl` / `x-default`), `preconnect`/`dns-prefetch` a los CDN, y **JSON-LD** (`GovernmentOrganization` con dirección y redes, más `WebSite` con `SearchAction`).

Problemas detectados:

- El `SearchAction` apunta a `https://laserena.clbuscar?q=...` (falta la barra: debería ser `laserena.cl/buscar`).
- Como es una SPA sin render en servidor, **el contenido no existe para un crawler que no ejecute JS**; el SEO real depende de que Google ejecute el bundle.
- `robots.txt` y `sitemap.xml` no existen (devuelven el HTML del portal).

### 10.3 PWA

- Se enlaza `/site.webmanifest` y se declaran favicons/apple-touch/mask-icon, pero **el manifest no existe** (el servidor devuelve `index.html`).
- `theme-color` = `#920000`, distinto del rojo base del CSS.

---

## 11. Hallazgos y observaciones

- **CSS propio por `@import` cross-domain:** si `framework.laserena.cl` cae o tarda, el portal queda sin estilos y el render se bloquea.
- **Bundle único de ~309 KB sin code-splitting:** coste de carga inicial alto para un portal informativo con rutas independientes.
- **Identidad de color inconsistente:** `#AD0000` (CSS) frente a `#920000` (theme-color y mask-icon).
- **Metadatos ausentes:** manifest, robots.txt y sitemap.xml no existen pese a estar referenciados.
- **Rutas irregulares:** `tramitesMunicipales` sin barra inicial y comodines `:parent/:child` que pueden pisarse con `/contenido/:slug`.
- **Leaflet desalineado:** se cargan CSS/JS 1.9.4 desde cdnjs, pero el código referencia iconos de marcador de la 1.7.1 (`cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/...`).
- **Bootstrap y Bootstrap Icons por CDN** con `integrity`: dependencia de red externa; si el CDN cambia, se rompe el layout (el `@import` del framework mitiga solo en parte).
- **Buenas prácticas presentes:** `rel="noopener noreferrer"` en enlaces externos, `integrity`+`crossorigin` en los CDN, y Consent Mode antes de cargar Analytics.
- **jQuery se usa solo en el admin** (`framework.laserena.cl` con DataTables), no en el portal público.

---

## 12. Evidencia

Archivos y endpoints revisados directamente:

- `https://laserena.cl/` — HTML del `<head>`, dependencias, JSON-LD, rutas de assets.
- `/assets/index-DklO5CaO.js` — bundle de la app (309 483 bytes).
- `/assets/index-Db2lHjC1.css` — estilos del portal (27 775 bytes).
- `https://framework.laserena.cl/css/frameworkV1.css` — design system (15 312 bytes).
- `https://framework.laserena.cl/js/frameworkV1.js` — HTML del admin "Framework".
- `https://framework.laserena.cl/templates/footer.html` y `transparencia.html`.
- `https://apis.munilaserena.cl/api-portal/menus`, `.../carruselPortal`, `.../tramitesPortal` (consultados con cabeceras de origen).
- Cabeceras HTTP de `laserena.cl` y `framework.laserena.cl`.

Captura renderizada de la portada: `home.png` (1440×4000, headless Firefox con perfil aislado). No interpretada por falta de visión en esta sesión; disponible para inspección manual.
