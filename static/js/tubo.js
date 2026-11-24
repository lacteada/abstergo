/* Kanban del Tubo de trabajo: arrastrar mueve y reordena sin recargar.

   Usa Pointer Events, así funciona con mouse, dedo y lápiz. Al arrastrar aparece
   un marcador en el punto de destino y una copia que sigue al puntero; al soltar,
   la tarjeta se mueve en el DOM con una animación corta y se envía el estado y el
   orden. No se recarga la página: solo se actualizan los contadores. Si el
   servidor rechaza, la tarjeta vuelve a su lugar. Solo se puede arrastrar con
   permiso de escritura (`data-escribir`).
*/
(function () {
  "use strict";

  var kanban = document.querySelector("[data-kanban]");
  if (!kanban) return;

  var escribir = kanban.dataset.escribir === "1";
  var arrastrada = null;
  var origen = null;
  var clon = null;
  var marca = null;
  var inicio = null; // punto donde empezó el puntero
  var desfase = { x: 0, y: 0 };
  var activo = false;

  function csrf() {
    var m = document.cookie.match(/(^|;)\s*csrftoken=([^;]+)/);
    return m ? decodeURIComponent(m[2]) : "";
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

  function pksDe(lista) {
    return Array.prototype.map.call(
      lista.querySelectorAll(".kanban-tarjeta"),
      function (t) {
        return t.dataset.pk;
      }
    );
  }

  function tarjetas(lista) {
    return Array.prototype.filter.call(
      lista.querySelectorAll(".kanban-tarjeta"),
      function (t) {
        return t !== arrastrada;
      }
    );
  }

  function listaBajoPunto(x, y) {
    var nodo = document.elementFromPoint(x, y);
    return nodo ? nodo.closest("[data-lista]") : null;
  }

  function trasPunto(lista, y) {
    var candidatas = tarjetas(lista);
    for (var i = 0; i < candidatas.length; i++) {
      var caja = candidatas[i].getBoundingClientRect();
      if (y < caja.top + caja.height / 2) return candidatas[i];
    }
    return null;
  }

  function actualizarContadores() {
    kanban.querySelectorAll("[data-lista]").forEach(function (lista) {
      var columna = lista.closest(".kanban-columna");
      var total = lista.querySelectorAll(".kanban-tarjeta").length;
      var contador = columna && columna.querySelector(".kanban-contador");
      if (contador) contador.textContent = total;
      var vacio = lista.querySelector(".kanban-vacio");
      if (total === 0 && !vacio) {
        var li = document.createElement("li");
        li.className = "kanban-vacio";
        li.textContent = lista.dataset.vacio || "Sin registros";
        lista.appendChild(li);
      } else if (total > 0 && vacio) {
        vacio.remove();
      }
    });
  }

  // Animación FLIP: las tarjetas se deslizan a su nueva posición.
  function animar(antes) {
    kanban.querySelectorAll(".kanban-tarjeta").forEach(function (t) {
      var previo = antes.get(t);
      if (!previo) return;
      var nuevo = t.getBoundingClientRect();
      var dx = previo.left - nuevo.left;
      var dy = previo.top - nuevo.top;
      if (!dx && !dy) return;
      t.animate(
        [{ transform: "translate(" + dx + "px," + dy + "px)" }, { transform: "none" }],
        { duration: 180, easing: "ease" }
      );
    });
  }

  function posiciones() {
    var mapa = new Map();
    kanban.querySelectorAll(".kanban-tarjeta").forEach(function (t) {
      mapa.set(t, t.getBoundingClientRect());
    });
    return mapa;
  }

  function enviarMovimiento(url, lista) {
    var datos = new FormData();
    datos.append("estado", lista.dataset.lista);
    datos.append("orden", pksDe(lista).join(","));
    return enviar(url, datos);
  }

  function empezar(evento) {
    if (!escribir || evento.button > 0) return;
    arrastrada = evento.currentTarget;
    origen = arrastrada.parentNode;
    inicio = { x: evento.clientX, y: evento.clientY };
    activo = false;
    document.addEventListener("pointermove", alMover);
    document.addEventListener("pointerup", alSoltar, { once: true });
  }

  function activar(evento) {
    var caja = arrastrada.getBoundingClientRect();
    desfase = { x: evento.clientX - caja.left, y: evento.clientY - caja.top };
    clon = arrastrada.cloneNode(true);
    clon.classList.add("kanban-clon");
    clon.style.width = caja.width + "px";
    document.body.appendChild(clon);
    marca = document.createElement("li");
    marca.className = "kanban-marca";
    arrastrada.classList.add("kanban-arrastrando");
    arrastrada.parentNode.insertBefore(marca, arrastrada);
    document.body.classList.add("arrastrando-kanban");
  }

  function alMover(evento) {
    if (!arrastrada) return;
    if (!activo) {
      var lejos =
        Math.abs(evento.clientX - inicio.x) + Math.abs(evento.clientY - inicio.y);
      if (lejos < 6) return;
      activo = true;
      activar(evento);
    }
    clon.style.transform =
      "translate(" + (evento.clientX - desfase.x) + "px," + (evento.clientY - desfase.y) + "px)";
    var lista = listaBajoPunto(evento.clientX, evento.clientY);
    if (lista) lista.insertBefore(marca, trasPunto(lista, evento.clientY));
  }

  function alSoltar() {
    document.removeEventListener("pointermove", alMover);
    if (!arrastrada) return;
    if (!activo) {
      arrastrada = null;
      return;
    }
    var tarjeta = arrastrada;
    var lista = marca.parentNode;
    var antes = posiciones();
    lista.insertBefore(tarjeta, marca);
    marca.remove();
    clon.remove();
    tarjeta.classList.remove("kanban-arrastrando");
    document.body.classList.remove("arrastrando-kanban");
    actualizarContadores();
    animar(antes);

    var volverAlOrigen = origen;
    enviarMovimiento(tarjeta.dataset.mover, lista)
      .then(function (resultado) {
        if (!resultado.ok) {
          volverAlOrigen.insertBefore(tarjeta, volverAlOrigen.firstChild);
          actualizarContadores();
          avisar(
            (resultado.cuerpo && resultado.cuerpo.error) ||
              "No se pudo mover la tarjeta."
          );
        }
      })
      .catch(function () {
        volverAlOrigen.insertBefore(tarjeta, volverAlOrigen.firstChild);
        actualizarContadores();
        avisar("No se pudo mover la tarjeta.");
      });

    arrastrada = null;
    activo = false;
    clon = null;
    marca = null;
  }

  function alAccion(evento) {
    var boton = evento.currentTarget;
    var tarjeta = boton.closest(".kanban-tarjeta");
    var antes = posiciones();
    boton.disabled = true;
    var lista = kanban.querySelector('[data-lista="' + boton.dataset.estado + '"]');
    if (!lista) return;
    lista.appendChild(tarjeta);
    actualizarContadores();
    animar(antes);
    enviarMovimiento(boton.dataset.mover, lista)
      .then(function (resultado) {
        if (!resultado.ok) {
          boton.disabled = false;
          avisar("No se pudo mover la tarjeta.");
          return;
        }
        boton.remove();
      })
      .catch(function () {
        boton.disabled = false;
        avisar("No se pudo mover la tarjeta.");
      });
  }

  function alReasignar(evento) {
    evento.preventDefault();
    var formulario = evento.currentTarget;
    enviar(formulario.getAttribute("action"), new FormData(formulario))
      .then(function (resultado) {
        if (resultado.ok && window.Mensajes) window.Mensajes.avisar("ok", "Reasignado.");
        else avisar("No se pudo reasignar.");
      })
      .catch(function () {
        avisar("No se pudo reasignar.");
      });
  }

  if (escribir) {
    kanban.querySelectorAll(".kanban-tarjeta").forEach(function (tarjeta) {
      tarjeta.addEventListener("pointerdown", empezar);
    });
  }
  kanban.querySelectorAll("[data-accion]").forEach(function (boton) {
    boton.addEventListener("click", alAccion);
  });
  kanban.querySelectorAll(".kanban-reasignar").forEach(function (formulario) {
    formulario.addEventListener("submit", alReasignar);
  });
})();
