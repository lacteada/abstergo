/* Buscador en los campos de selección (selects de llave foránea).

   Convierte cada <select data-autocomplete> en un combobox: un input de texto
   que consulta el motor por nombre/RUT y arma la lista. El select sigue siendo
   el control del formulario (el valor que se envía), así el POST no cambia.
   Sin este script queda el select completo de siempre.
*/
(function () {
  "use strict";

  var DEBOUNCE = 250;

  function textoDe(select) {
    var opcion = select.options[select.selectedIndex];
    return opcion ? opcion.textContent.trim() : "";
  }

  function mejorar(select) {
    if (select.dataset.autocompletadoListo) return;
    select.dataset.autocompletadoListo = "1";
    var url = select.dataset.autocomplete;

    var caja = document.createElement("div");
    caja.className = "fkBuscable";
    select.parentNode.insertBefore(caja, select);

    var entrada = document.createElement("input");
    entrada.type = "text";
    entrada.className = "fkBuscable-campo";
    entrada.autocomplete = "off";
    entrada.placeholder = "Buscar…";
    entrada.value = textoDe(select);
    if (select.disabled) entrada.disabled = true;

    var lista = document.createElement("ul");
    lista.className = "fkBuscable-lista";
    lista.hidden = true;

    caja.appendChild(entrada);
    caja.appendChild(lista);
    caja.appendChild(select);
    select.classList.add("fkBuscable-select");

    function cerrar() {
      lista.hidden = true;
    }

    function elegir(id, texto) {
      select.value = String(id);
      select.dispatchEvent(new Event("change", { bubbles: true }));
      entrada.value = texto;
      cerrar();
    }

    function pintar(resultados) {
      while (lista.firstChild) lista.removeChild(lista.firstChild);
      if (select.querySelector('option[value=""]')) {
        var vacio = document.createElement("li");
        vacio.textContent = "— Ninguno —";
        vacio.addEventListener("mousedown", function (evento) {
          evento.preventDefault();
          elegir("", "");
        });
        lista.appendChild(vacio);
      }
      resultados.forEach(function (resultado) {
        var item = document.createElement("li");
        item.textContent = resultado.text;
        item.addEventListener("mousedown", function (evento) {
          evento.preventDefault();
          elegir(resultado.id, resultado.text);
        });
        lista.appendChild(item);
      });
      lista.hidden = resultados.length === 0;
    }

    var temporizador = null;

    function consultar() {
      var consulta = entrada.value.trim();
      fetch(url + "?q=" + encodeURIComponent(consulta))
        .then(function (respuesta) {
          return respuesta.json();
        })
        .then(function (datos) {
          pintar(datos.resultados || []);
        })
        .catch(function () {
          cerrar();
        });
    }

    entrada.addEventListener("input", function () {
      clearTimeout(temporizador);
      temporizador = setTimeout(consultar, DEBOUNCE);
    });
    entrada.addEventListener("focus", consultar);
    entrada.addEventListener("blur", function () {
      // Deja margen para el mousedown de la opción.
      setTimeout(cerrar, 150);
    });
  }

  function iniciar(raiz) {
    raiz.querySelectorAll("select[data-autocomplete]").forEach(mejorar);
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
