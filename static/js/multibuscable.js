/* Select múltiple con buscador (etiquetas).

   Convierte cada <select multiple data-multibuscable> en una caja de etiquetas:
   se busca por nombre o RUT y se agregan/quitan a gusto. El <select> sigue
   siendo el control del formulario, así el POST no cambia. Sin este script
   queda el select múltiple de siempre.
*/
(function () {
  "use strict";

  var DEBOUNCE = 250;

  function mejorar(select) {
    if (select.dataset.multibuscableListo) return;
    select.dataset.multibuscableListo = "1";
    var url = select.dataset.url;
    select.classList.add("multibuscable-select");

    var caja = document.createElement("div");
    caja.className = "multibuscable";
    var chips = document.createElement("div");
    chips.className = "multibuscable-chips";
    var entrada = document.createElement("input");
    entrada.type = "text";
    entrada.className = "multibuscable-campo";
    entrada.placeholder = "Buscar…";
    entrada.autocomplete = "off";
    var lista = document.createElement("ul");
    lista.className = "multibuscable-lista";
    lista.hidden = true;

    caja.appendChild(chips);
    caja.appendChild(entrada);
    caja.appendChild(lista);
    select.parentNode.insertBefore(caja, select);
    caja.appendChild(select);

    function seleccionadas() {
      return Array.prototype.filter.call(select.options, function (o) {
        return o.selected;
      });
    }

    function pintarChips() {
      chips.innerHTML = "";
      seleccionadas().forEach(function (op) {
        var chip = document.createElement("span");
        chip.className = "chip";
        var texto = document.createElement("span");
        texto.textContent = op.textContent.trim();
        var quitar = document.createElement("button");
        quitar.type = "button";
        quitar.className = "chip-quitar";
        quitar.textContent = "×";
        quitar.setAttribute("aria-label", "Quitar " + texto.textContent);
        quitar.addEventListener("click", function () {
          op.selected = false;
          pintarChips();
        });
        chip.appendChild(texto);
        chip.appendChild(quitar);
        chips.appendChild(chip);
      });
    }

    function agregar(id, texto) {
      var op = Array.prototype.find.call(select.options, function (o) {
        return o.value === String(id);
      });
      if (!op) {
        op = document.createElement("option");
        op.value = String(id);
        op.textContent = texto;
        select.appendChild(op);
      }
      op.selected = true;
      pintarChips();
    }

    function pintarResultados(items) {
      lista.innerHTML = "";
      items.forEach(function (r) {
        var li = document.createElement("li");
        li.textContent = r.text;
        li.addEventListener("mousedown", function (evento) {
          evento.preventDefault();
          agregar(r.id, r.text);
          entrada.value = "";
          lista.hidden = true;
        });
        lista.appendChild(li);
      });
      lista.hidden = items.length === 0;
    }

    var temporizador = null;
    function consultar() {
      fetch(url + "?q=" + encodeURIComponent(entrada.value.trim()))
        .then(function (r) {
          return r.json();
        })
        .then(function (datos) {
          pintarResultados(datos.resultados || []);
        })
        .catch(function () {
          lista.hidden = true;
        });
    }

    entrada.addEventListener("input", function () {
      clearTimeout(temporizador);
      temporizador = setTimeout(consultar, DEBOUNCE);
    });
    entrada.addEventListener("focus", consultar);
    entrada.addEventListener("blur", function () {
      setTimeout(function () {
        lista.hidden = true;
      }, 150);
    });

    pintarChips();
  }

  function iniciar(raiz) {
    raiz.querySelectorAll("select[data-multibuscable]").forEach(mejorar);
  }

  function arrancar() {
    iniciar(document);
    var dialogo = document.querySelector("[data-modal-dialog]");
    if (dialogo && window.MutationObserver) {
      new MutationObserver(function () {
        iniciar(dialogo);
      }).observe(dialogo, { childList: true });
    }
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", arrancar);
  } else {
    arrancar();
  }
})();
