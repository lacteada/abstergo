/* Calendario en los campos de fecha (flatpickr, vendorizado local).

   Inicializa todo <input type="date"> y <input type="datetime-local"> del
   documento, incluido el modal, que reemplaza su contenido al abrir. El formato
   de salida sigue siendo el que Django espera, así que el POST no cambia. Sin
   este script el navegador muestra su calendario nativo.
*/
(function () {
  "use strict";

  if (typeof flatpickr !== "function") return;

  var COMUN = { locale: "es", allowInput: true };

  function activar(raiz) {
    raiz.querySelectorAll('input[type="date"]').forEach(function (campo) {
      if (campo.dataset.fechaLista) return;
      campo.dataset.fechaLista = "1";
      flatpickr(campo, Object.assign({ dateFormat: "Y-m-d" }, COMUN));
    });
    raiz.querySelectorAll('input[type="datetime-local"]').forEach(function (campo) {
      if (campo.dataset.fechaLista) return;
      campo.dataset.fechaLista = "1";
      flatpickr(
        campo,
        Object.assign(
          { enableTime: true, time_24hr: true, dateFormat: "Y-m-d\\TH:i" },
          COMUN
        )
      );
    });
  }

  function iniciar() {
    activar(document);
    var dialogo = document.querySelector("[data-modal-dialog]");
    if (dialogo && window.MutationObserver) {
      new MutationObserver(function () {
        activar(dialogo);
      }).observe(dialogo, { childList: true });
    }
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", iniciar);
  } else {
    iniciar();
  }
})();
