/* CRUD en un modal nativo <dialog>.

   Los disparadores [data-modal] piden la vista del formulario como fragmento
   (encabezado X-Modal) y lo inyectan en el diálogo. Dentro del modal:

   - Un formulario GET (el buscador de "Crear Atención") y los enlaces internos
     (los resultados de vecinos, que son `?vecino=`) recargan el diálogo, no la
     página.
   - El formulario POST se envía por fetch: si la vista responde con
     redirección (éxito), se cierra el modal y se refrescan las filas, el
     contador y el paginador del listado; si vuelve con 200 (errores de
     validación), se reemplaza el contenido del modal.

   Sin este script, los enlaces [data-modal] abren las páginas completas de
   siempre: la degradación es automática.
*/
(function () {
  const dialogo = document.querySelector("[data-modal-dialog]");
  if (!dialogo || typeof dialogo.showModal !== "function") return;

  const SELECTORES = ["[data-filas]", "[data-pie]", "[data-paginacion]"];
  let urlActual = ""; // dirección del fragmento que hay en el diálogo

  function cerrar() {
    if (dialogo.open) dialogo.close();
    dialogo.innerHTML = "";
    urlActual = "";
  }

  function extraerAvisos(documento) {
    const avisos = documento.querySelector("[data-mensajes]");
    if (!avisos || !window.Mensajes) return;
    avisos.querySelectorAll("[data-nivel]").forEach(function (nodo) {
      window.Mensajes.avisar(nodo.dataset.nivel, nodo.textContent.trim());
    });
  }

  function refrescarListado() {
    fetch(window.location.href, { headers: { "X-Modal": "1" } })
      .then(function (respuesta) {
        return respuesta.text();
      })
      .then(function (html) {
        const documento = new DOMParser().parseFromString(html, "text/html");
        SELECTORES.forEach(function (selector) {
          const actual = document.querySelector(selector);
          const nuevo = documento.querySelector(selector);
          if (actual && nuevo) actual.innerHTML = nuevo.innerHTML;
        });
        extraerAvisos(documento);
      })
      .catch(function () {
        // Si falla la red, la fila queda como estaba; se refresca al navegar.
      });
  }

  // Navegación interna del modal: pide otro fragmento y reemplaza el diálogo.
  function cargar(url) {
    urlActual = url;
    fetch(url, { headers: { "X-Modal": "1" } })
      .then(function (respuesta) {
        return respuesta.text();
      })
      .then(function (html) {
        dialogo.innerHTML = html;
      })
      .catch(function () {
        cerrar();
      });
  }

  function abrir(url) {
    dialogo.innerHTML = '<p class="modal-cargando">Cargando…</p>';
    dialogo.showModal();
    cargar(url);
  }

  document.addEventListener("click", function (evento) {
    if (evento.target.closest("[data-modal-cerrar]")) {
      evento.preventDefault();
      cerrar();
      return;
    }
    const disparador = evento.target.closest("[data-modal]");
    if (disparador) {
      evento.preventDefault();
      abrir(disparador.dataset.modal || disparador.getAttribute("href"));
    }
  });

  dialogo.addEventListener("click", function (evento) {
    // Un clic en el fondo (fuera de la tarjeta) cierra el modal.
    if (evento.target === dialogo) {
      cerrar();
      return;
    }
    // Enlaces internos del flujo (por ejemplo `?vecino=3`): se quedan en el modal.
    const enlace = evento.target.closest("a[href]");
    const href = enlace ? enlace.getAttribute("href") : "";
    if (href.charAt(0) === "?") {
      evento.preventDefault();
      cargar(urlActual.split("?")[0] + href);
    }
  });

  dialogo.addEventListener("submit", function (evento) {
    const formulario = evento.target;
    if (!(formulario instanceof HTMLFormElement)) return;
    evento.preventDefault();

    const metodo = (formulario.getAttribute("method") || "get").toLowerCase();
    if (metodo === "get") {
      const consulta = new URLSearchParams(new FormData(formulario)).toString();
      const accion = formulario.getAttribute("action") || urlActual.split("?")[0];
      cargar(accion + (consulta ? "?" + consulta : ""));
      return;
    }

    const accion = formulario.getAttribute("action") || window.location.href;
    fetch(accion, {
      method: "POST",
      body: new FormData(formulario),
      headers: { "X-Modal": "1" },
    })
      .then(function (respuesta) {
        if (respuesta.redirected) {
          // El fetch ya siguió la redirección al listado: ahí vienen las
          // messages (que solo se pueden leer una vez), así que los avisos se
          // sacan de esta respuesta y luego se refresca conservando el filtro.
          cerrar();
          return respuesta.text().then(function (html) {
            extraerAvisos(new DOMParser().parseFromString(html, "text/html"));
            refrescarListado();
            return null;
          });
        }
        return respuesta.text();
      })
      .then(function (html) {
        if (html !== null && html !== undefined) dialogo.innerHTML = html;
      })
      .catch(function () {
        cerrar();
      });
  });
})();
