/* Convierte las acciones de fila en botones.

   Las acciones del CRUD se marcan como enlaces para degradar sin JavaScript;
   acá se convierten en <button> reales, conservando sus clases y atributos (el
   enlace guarda la dirección en data-url y reenvía los data-* de la acción).
   Si este script no corre, el enlace sigue funcionando como siempre.
*/
(function () {
  "use strict";

  function convertir(enlace) {
    var boton = document.createElement("button");
    boton.type = "button";
    boton.className = enlace.className;
    ["title", "aria-label"].forEach(function (nombre) {
      if (enlace.hasAttribute(nombre)) {
        boton.setAttribute(nombre, enlace.getAttribute(nombre));
      }
    });
    var destino = enlace.getAttribute("href") || "";
    boton.dataset.url = destino;
    if (enlace.hasAttribute("data-modal")) boton.dataset.modal = destino;
    if (enlace.hasAttribute("data-desactivar")) boton.dataset.desactivar = "";
    if (enlace.hasAttribute("data-reactivar")) boton.dataset.reactivar = "";
    if (enlace.hasAttribute("data-eliminar")) boton.dataset.eliminar = "";
    boton.innerHTML = enlace.innerHTML;
    enlace.replaceWith(boton);
  }

  function iniciar(raiz) {
    raiz.querySelectorAll(".acciones-lista a.accion").forEach(convertir);
  }

  function arrancar() {
    iniciar(document);
    // La búsqueda en vivo reemplaza las filas: hay que reconvertir.
    var filas = document.querySelector("[data-filas]");
    if (filas && window.MutationObserver) {
      new MutationObserver(function () {
        iniciar(filas);
      }).observe(filas, { childList: true });
    }
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", arrancar);
  } else {
    arrancar();
  }
})();
