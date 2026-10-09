/* CRUD en un modal nativo <dialog>.

   Los disparadores [data-modal] piden la vista del formulario como fragmento
   (encabezado X-Modal) y lo inyectan en el diálogo. El envío también va por
   fetch: si la vista responde con redirección (éxito), se cierra el modal y se
   refrescan las filas, el contador y el paginador del listado sin recargar; si
   vuelve con 200 (errores de validación), se reemplaza el contenido del modal.

   Sin este script, los enlaces [data-modal] abren las páginas completas de
   siempre: la degradación es automática.
*/
(function () {
  const dialogo = document.querySelector("[data-modal-dialog]");
  if (!dialogo || typeof dialogo.showModal !== "function") return;

  const SELECTORES = ["[data-filas]", "[data-pie]", "[data-paginacion]"];

  function cerrar() {
    if (dialogo.open) dialogo.close();
    dialogo.innerHTML = "";
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

  function abrir(url) {
    dialogo.innerHTML = '<p class="modal-cargando">Cargando…</p>';
    dialogo.showModal();
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

  dialogo.addEventListener("submit", function (evento) {
    if (!(evento.target instanceof HTMLFormElement)) return;
    evento.preventDefault();
    const formulario = evento.target;
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

  // Un clic en el fondo (fuera de la tarjeta) cierra el modal.
  dialogo.addEventListener("click", function (evento) {
    if (evento.target === dialogo) cerrar();
  });
})();
