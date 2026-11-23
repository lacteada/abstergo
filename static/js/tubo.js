// Kanban del Tubo de trabajo: arrastrar una tarjeta cambia su estado.
(function () {
  "use strict";

  var kanban = document.querySelector("[data-kanban]");
  if (!kanban) {
    return;
  }

  function csrf() {
    var match = document.cookie.match(/(^|;)\s*csrftoken=([^;]+)/);
    return match ? decodeURIComponent(match[2]) : "";
  }

  // Envía la acción por fetch; recarga para reflejar el estado ya sea que
  // resulte bien o mal (el servidor valida las transiciones).
  function enviar(url, datos) {
    return fetch(url, {
      method: "POST",
      headers: { "X-CSRFToken": csrf() },
      body: datos,
    });
  }

  function recargar() {
    window.location.reload();
  }

  var arrastrada = null;

  kanban.querySelectorAll(".kanban-tarjeta").forEach(function (tarjeta) {
    tarjeta.addEventListener("dragstart", function () {
      arrastrada = tarjeta;
      tarjeta.classList.add("arrastrando");
    });
    tarjeta.addEventListener("dragend", function () {
      tarjeta.classList.remove("arrastrando");
      arrastrada = null;
    });
  });

  kanban.querySelectorAll("[data-lista]").forEach(function (lista) {
    lista.addEventListener("dragover", function (evento) {
      evento.preventDefault();
    });
    lista.addEventListener("drop", function (evento) {
      evento.preventDefault();
      if (!arrastrada) {
        return;
      }
      var datos = new FormData();
      datos.append("estado", lista.getAttribute("data-lista"));
      enviar(arrastrada.getAttribute("data-mover"), datos).then(recargar, recargar);
    });
  });

  // Botón de acción de cada tarjeta ("A Pendiente", "A Proceso", "Realizar").
  kanban.querySelectorAll("[data-accion]").forEach(function (boton) {
    boton.addEventListener("click", function () {
      var tarjeta = boton.closest(".kanban-tarjeta");
      var datos = new FormData();
      datos.append("estado", boton.getAttribute("data-estado"));
      boton.disabled = true;
      enviar(tarjeta.getAttribute("data-mover"), datos).then(recargar, recargar);
    });
  });

  // Reasignación del responsable desde la tarjeta (RF-053).
  kanban.querySelectorAll(".kanban-reasignar").forEach(function (form) {
    form.addEventListener("submit", function (evento) {
      evento.preventDefault();
      enviar(form.getAttribute("action"), new FormData(form)).then(recargar, recargar);
    });
  });
})();
