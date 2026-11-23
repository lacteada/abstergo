/* Kanban del Tubo de trabajo: arrastrar mueve y reordena sin recargar la página.

   Al soltar, la tarjeta se mueve en el DOM de inmediato (respuesta instantánea),
   se envía el nuevo estado y el orden de la columna destino, y al confirmar el
   servidor se refresca solo el tablero (no toda la página). Si el servidor
   rechaza el movimiento, la tarjeta vuelve a su lugar y se avisa.

   Sirve igual para el tablero de tareas y el de cartas: todo va por [data-kanban].
*/
(function () {
  "use strict";

  var kanban = document.querySelector("[data-kanban]");
  if (!kanban) return;

  function csrf() {
    var match = document.cookie.match(/(^|;)\s*csrftoken=([^;]+)/);
    return match ? decodeURIComponent(match[2]) : "";
  }

  function listaDe(estado) {
    return kanban.querySelector('[data-lista="' + estado + '"]');
  }

  function pksDe(lista) {
    return Array.prototype.map.call(
      lista.querySelectorAll(".kanban-tarjeta"),
      function (tarjeta) {
        return tarjeta.dataset.pk;
      }
    );
  }

  function avisar(mensaje) {
    if (window.Mensajes) window.Mensajes.avisar("error", mensaje);
  }

  function enviar(url, datos) {
    return fetch(url, {
      method: "POST",
      headers: { "X-CSRFToken": csrf() },
      body: datos,
    }).then(function (respuesta) {
      return respuesta.json().then(function (cuerpo) {
        return { ok: respuesta.ok, cuerpo: cuerpo };
      });
    });
  }

  // Reemplaza el tablero por el estado del servidor, sin recargar la página.
  function refrescar() {
    return fetch(window.location.href)
      .then(function (respuesta) {
        return respuesta.text();
      })
      .then(function (html) {
        var documento = new DOMParser().parseFromString(html, "text/html");
        var nuevo = documento.querySelector("[data-kanban]");
        if (nuevo) kanban.innerHTML = nuevo.innerHTML;
        enganchar();
      })
      .catch(function () {});
  }

  var arrastrada = null;

  // La tarjeta ante la cual insertar, según dónde va el cursor.
  function trasCursor(lista, y) {
    var candidatas = Array.prototype.slice.call(
      lista.querySelectorAll(".kanban-tarjeta:not(.arrastrando)")
    );
    for (var i = 0; i < candidatas.length; i++) {
      var caja = candidatas[i].getBoundingClientRect();
      if (y < caja.top + caja.height / 2) return candidatas[i];
    }
    return null;
  }

  function mover(tarjeta, destino, antesDe) {
    var lista = listaDe(destino);
    if (!lista) return;
    var origen = tarjeta.parentNode;
    lista.insertBefore(tarjeta, antesDe || null);
    var datos = new FormData();
    datos.append("estado", destino);
    datos.append("orden", pksDe(lista).join(","));
    enviar(tarjeta.dataset.mover, datos)
      .then(function (resultado) {
        if (!resultado.ok) {
          origen.appendChild(tarjeta);
          avisar(
            (resultado.cuerpo && resultado.cuerpo.error) ||
              "No se pudo mover la tarjeta."
          );
          return;
        }
        refrescar();
      })
      .catch(function () {
        origen.appendChild(tarjeta);
        avisar("No se pudo mover la tarjeta.");
      });
  }

  function alSoltar(evento) {
    evento.preventDefault();
    if (!arrastrada) return;
    var lista = evento.currentTarget;
    mover(arrastrada, lista.dataset.lista, trasCursor(lista, evento.clientY));
  }

  function alAccion(evento) {
    var boton = evento.currentTarget;
    var tarjeta = boton.closest(".kanban-tarjeta");
    boton.disabled = true;
    mover(tarjeta, boton.dataset.estado, null);
  }

  function alReasignar(evento) {
    evento.preventDefault();
    var formulario = evento.currentTarget;
    enviar(formulario.getAttribute("action"), new FormData(formulario))
      .then(function (resultado) {
        if (!resultado.ok) {
          avisar("No se pudo reasignar.");
          return;
        }
        refrescar();
      })
      .catch(function () {
        avisar("No se pudo reasignar.");
      });
  }

  // Idempotente: marca cada nodo ya enganchado, así el refresco no duplica.
  function enganchar() {
    kanban.querySelectorAll(".kanban-tarjeta").forEach(function (tarjeta) {
      if (tarjeta.dataset.enganchada) return;
      tarjeta.dataset.enganchada = "1";
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
      if (lista.dataset.enganchada) return;
      lista.dataset.enganchada = "1";
      lista.addEventListener("dragover", function (evento) {
        evento.preventDefault();
      });
      lista.addEventListener("drop", alSoltar);
    });
    kanban.querySelectorAll("[data-accion]").forEach(function (boton) {
      if (boton.dataset.enganchada) return;
      boton.dataset.enganchada = "1";
      boton.addEventListener("click", alAccion);
    });
    kanban.querySelectorAll(".kanban-reasignar").forEach(function (formulario) {
      if (formulario.dataset.enganchada) return;
      formulario.dataset.enganchada = "1";
      formulario.addEventListener("submit", alReasignar);
    });
  }

  enganchar();
})();
