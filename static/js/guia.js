/* Guía de bienvenida: tour por pasos con resaltado. Sin dependencias.
   Los pasos llegan en un <script id="guia-pasos"> y el contenedor trae la URL
   a la que se avisa que la guía ya se vio. */
(function () {
  "use strict";

  var contenedor = document.querySelector("[data-guia]");
  var datos = document.getElementById("guia-pasos");
  if (!contenedor || !datos) return;

  var pasos;
  try {
    pasos = JSON.parse(datos.textContent);
  } catch (e) {
    return;
  }
  pasos = pasos
    .map(function (paso) {
      return { paso: paso, el: document.querySelector(paso.selector) };
    })
    .filter(function (item) {
      return item.el;
    });
  if (!pasos.length) return;

  var indice = 0;

  var foco = document.createElement("div");
  foco.className = "guia-foco";
  var tarjeta = document.createElement("div");
  tarjeta.className = "guia-tarjeta";
  tarjeta.setAttribute("role", "dialog");
  tarjeta.setAttribute("aria-label", "Guía de bienvenida");
  document.body.appendChild(foco);
  document.body.appendChild(tarjeta);

  function csrf() {
    var cookie = document.cookie.match(/(^|;)\s*csrftoken=([^;]+)/);
    if (cookie) return decodeURIComponent(cookie[2]);
    var input = document.querySelector("input[name=csrfmiddlewaretoken]");
    return input ? input.value : "";
  }

  function avisar() {
    try {
      fetch(contenedor.dataset.url, {
        method: "POST",
        headers: { "X-CSRFToken": csrf() },
        credentials: "same-origin",
      });
    } catch (e) {
      /* el aviso no es crítico */
    }
  }

  function cerrar() {
    avisar();
    foco.remove();
    tarjeta.remove();
    window.removeEventListener("resize", ubicar);
    window.removeEventListener("scroll", ubicar, true);
    document.removeEventListener("keydown", teclas);
  }

  function ubicar() {
    var item = pasos[indice];
    var el = item.el;
    if (el.tagName === "DETAILS") el.open = true;
    var caja = el.getBoundingClientRect();
    var margen = 6;
    foco.style.top = caja.top - margen + "px";
    foco.style.left = caja.left - margen + "px";
    foco.style.width = caja.width + margen * 2 + "px";
    foco.style.height = caja.height + margen * 2 + "px";

    var abajo = caja.bottom + 12;
    var alto = 200;
    if (abajo + alto > window.innerHeight && caja.top > alto) {
      tarjeta.style.top = "auto";
      tarjeta.style.bottom = window.innerHeight - caja.top + 12 + "px";
    } else {
      tarjeta.style.bottom = "auto";
      tarjeta.style.top = abajo + "px";
    }
    var ancho = 320;
    var izquierda = Math.min(
      Math.max(12, caja.left),
      window.innerWidth - ancho - 12
    );
    tarjeta.style.left = izquierda + "px";
  }

  function pintar() {
    var item = pasos[indice];
    var ultimo = indice === pasos.length - 1;
    tarjeta.innerHTML =
      '<div class="guia-paso">' +
      (indice + 1) +
      " de " +
      pasos.length +
      "</div>" +
      "<h3>" +
      item.paso.titulo +
      "</h3>" +
      "<p>" +
      item.paso.texto +
      "</p>" +
      '<div class="guia-botones">' +
      '<button type="button" class="guia-saltar">Saltar</button>' +
      '<span class="guia-espacio"></span>' +
      (indice > 0
        ? '<button type="button" class="guia-anterior">Anterior</button>'
        : "") +
      '<button type="button" class="guia-siguiente btn-muni">' +
      (ultimo ? "Finalizar" : "Siguiente") +
      "</button>" +
      "</div>";

    tarjeta.querySelector(".guia-saltar").addEventListener("click", cerrar);
    var atras = tarjeta.querySelector(".guia-anterior");
    if (atras) {
      atras.addEventListener("click", function () {
        indice -= 1;
        pintar();
        ubicar();
      });
    }
    tarjeta
      .querySelector(".guia-siguiente")
      .addEventListener("click", function () {
        if (ultimo) {
          cerrar();
        } else {
          indice += 1;
          pintar();
          ubicar();
        }
      });
    ubicar();
  }

  function teclas(evento) {
    if (evento.key === "Escape") cerrar();
    if (evento.key === "ArrowRight" && indice < pasos.length - 1) {
      indice += 1;
      pintar();
    }
    if (evento.key === "ArrowLeft" && indice > 0) {
      indice -= 1;
      pintar();
    }
  }

  window.addEventListener("resize", ubicar);
  window.addEventListener("scroll", ubicar, true);
  document.addEventListener("keydown", teclas);
  pintar();
})();
