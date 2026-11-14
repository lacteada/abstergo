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
      var estado = lista.getAttribute("data-lista");
      var destino = lista.querySelector(".kanban-vacio");
      if (destino) {
        destino.remove();
      }
      lista.appendChild(arrastrada);
      actualizarContadores();

      var datos = new FormData();
      datos.append("estado", estado);
      fetch(arrastrada.getAttribute("data-mover"), {
        method: "POST",
        headers: { "X-CSRFToken": csrf() },
        body: datos,
      }).catch(function () {
        window.location.reload();
      });
    });
  });

  function actualizarContadores() {
    kanban.querySelectorAll(".kanban-columna").forEach(function (columna) {
      var total = columna.querySelectorAll(".kanban-tarjeta").length;
      var contador = columna.querySelector(".kanban-contador");
      if (contador) {
        contador.textContent = total;
      }
    });
  }
})();
