/* Sidebar plegable: recuerda el estado de cada grupo y siempre abre el que
   contiene la sección activa. Sin dependencias. */
(function () {
  "use strict";

  var nav = document.querySelector("[data-nav]");
  if (!nav) return;

  var CLAVE = "abstergo:sidebar:";

  nav.querySelectorAll("[data-grupo]").forEach(function (grupo) {
    var clave = CLAVE + grupo.dataset.grupo;
    var tieneActivo = !!grupo.querySelector(".activo");
    var guardado = null;
    try {
      guardado = window.localStorage.getItem(clave);
    } catch (e) {
      guardado = null;
    }

    // La sección activa manda: ese grupo queda abierto aunque se haya
    // cerrado antes. El resto respeta lo guardado.
    if (tieneActivo) {
      grupo.open = true;
    } else if (guardado === "cerrado") {
      grupo.open = false;
    } else if (guardado === "abierto") {
      grupo.open = true;
    }

    grupo.addEventListener("toggle", function () {
      if (tieneActivo) return;
      try {
        window.localStorage.setItem(clave, grupo.open ? "abierto" : "cerrado");
      } catch (e) {
        /* sin localStorage disponible: se ignora */
      }
    });
  });

  // En pantallas angostas el menú se abre con un botón (menú off-canvas).
  var boton = document.querySelector("[data-menu-boton]");
  if (boton) {
    boton.addEventListener("click", function () {
      var app = document.querySelector(".app");
      var abierto = app.classList.toggle("menu-abierto");
      boton.setAttribute("aria-expanded", abierto ? "true" : "false");
    });
  }
})();
