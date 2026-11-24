/* Selector de persona (vecino): un botón «+» por cargo que abre un buscador.

   El <select> del campo queda oculto y el botón muestra a la persona elegida.
   Al abrir, se busca por nombre o RUT contra el mismo motor de autocompletado.
   Si no existe, se puede crear escribiendo nombre y RUT: esos valores van a los
   campos ocultos declarados en `data-crear` y el alta se guarda junto con el
   formulario (no al instante). Sin este script queda el select de siempre.
*/
(function () {
  "use strict";

  var DEBOUNCE = 250;
  var dialogo = null;
  var objetivo = null; // { select, url, crear:[nombreRut, ...], pintar }

  function porNombre(nombre) {
    return document.querySelector('[name="' + nombre + '"]');
  }

  function crearDialogo() {
    if (dialogo) return dialogo;
    dialogo = document.createElement("dialog");
    dialogo.className = "modal persona-modal";
    dialogo.innerHTML =
      '<div class="modal-cabecera">' +
      '<h2 class="modal-titulo" data-p-titulo>Elegir persona</h2>' +
      '<button class="modal-cerrar" type="button" data-p-cerrar aria-label="Cerrar">' +
      '<svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" ' +
      'stroke-width="2" stroke-linecap="round"><path d="M6 6l12 12M18 6L6 18"></path></svg>' +
      "</button></div>" +
      '<div class="modal-cuerpo">' +
      '<div class="campo"><label for="persona-buscar">Buscar por nombre o RUT</label>' +
      '<input id="persona-buscar" type="search" autocomplete="off" ' +
      'placeholder="Nombre o RUT" data-p-buscar></div>' +
      '<ul class="persona-resultados" data-p-resultados></ul>' +
      '<div class="persona-crear" data-p-crear hidden>' +
      '<p class="ayuda">No está en la lista. Escríbela y se guardará junto con el formulario.</p>' +
      '<div class="campo"><label for="persona-nombre">Nombre y apellido</label>' +
      '<input id="persona-nombre" type="text" data-p-nombre></div>' +
      '<div class="campo"><label for="persona-rut">RUT</label>' +
      '<input id="persona-rut" type="text" inputmode="numeric" ' +
      'placeholder="12345678-9" data-p-rut></div>' +
      '<button class="btn-muni" type="button" data-p-crear-go>Crear persona</button>' +
      "</div>" +
      '<p class="error" data-p-error hidden></p>' +
      "</div>";
    document.body.appendChild(dialogo);

    var buscar = dialogo.querySelector("[data-p-buscar]");
    var lista = dialogo.querySelector("[data-p-resultados]");
    var cajaCrear = dialogo.querySelector("[data-p-crear]");
    var nombreCrear = dialogo.querySelector("[data-p-nombre]");
    var rutCrear = dialogo.querySelector("[data-p-rut]");
    var error = dialogo.querySelector("[data-p-error]");
    var temporizador = null;

    function mostrarError(texto) {
      if (!texto) {
        error.hidden = true;
        return;
      }
      error.textContent = texto;
      error.hidden = false;
    }

    function limpiarCamposCrear() {
      objetivo.crear.forEach(function (nombre) {
        var campo = porNombre(nombre);
        if (campo) campo.value = "";
      });
    }

    function elegir(id) {
      objetivo.select.value = String(id);
      objetivo.select.dispatchEvent(new Event("change", { bubbles: true }));
      limpiarCamposCrear();
      objetivo.pintar();
      dialogo.close();
    }

    function pintar(items) {
      lista.innerHTML = "";
      items.forEach(function (r) {
        var li = document.createElement("li");
        li.className = "persona-resultado";
        li.textContent = r.text;
        li.addEventListener("click", function () {
          elegir(r.id);
        });
        lista.appendChild(li);
      });
      cajaCrear.hidden = items.length > 0;
      if (!cajaCrear.hidden && !nombreCrear.value) {
        nombreCrear.value = buscar.value.trim();
      }
    }

    function consultar() {
      mostrarError("");
      fetch(objetivo.url + "?q=" + encodeURIComponent(buscar.value.trim()))
        .then(function (r) {
          return r.json();
        })
        .then(function (datos) {
          pintar(datos.resultados || []);
        })
        .catch(function () {
          pintar([]);
        });
    }

    buscar.addEventListener("input", function () {
      clearTimeout(temporizador);
      temporizador = setTimeout(consultar, DEBOUNCE);
    });

    dialogo.querySelector("[data-p-cerrar]").addEventListener("click", function () {
      dialogo.close();
    });

    dialogo.querySelector("[data-p-crear-go]").addEventListener("click", function () {
      var nombre = nombreCrear.value.trim();
      var rut = rutCrear.value.trim();
      if (!nombre || !rut) {
        mostrarError("Indica nombre y RUT para crear la persona.");
        return;
      }
      objetivo.select.value = "";
      var valores = [nombre, rut];
      objetivo.crear.forEach(function (n, i) {
        var campo = porNombre(n);
        if (campo) campo.value = valores[i] || "";
      });
      objetivo.pintar();
      dialogo.close();
    });

    dialogo._reset = function () {
      buscar.value = "";
      nombreCrear.value = "";
      rutCrear.value = "";
      cajaCrear.hidden = true;
      lista.innerHTML = "";
      mostrarError("");
    };
    dialogo._buscar = buscar;
    dialogo._titulo = dialogo.querySelector("[data-p-titulo]");
    return dialogo;
  }

  function abrir(select, url, crear, etiqueta, pintarBoton) {
    var d = crearDialogo();
    objetivo = { select: select, url: url, crear: crear, pintar: pintarBoton };
    d._titulo.textContent = etiqueta ? "Elegir " + etiqueta : "Elegir persona";
    d._reset();
    d.showModal();
    d._buscar.focus();
  }

  function textoDe(select, crear) {
    var opcion = select.options[select.selectedIndex];
    if (select.value && opcion) return opcion.textContent.trim();
    var n = porNombre(crear[0]);
    var r = porNombre(crear[1]);
    if (n && n.value) {
      return n.value + (r && r.value ? " (" + r.value + ")" : "") + " · por crear";
    }
    return "";
  }

  function mejorar(select) {
    if (select.dataset.personaListo) return;
    select.dataset.personaListo = "1";
    var url = select.dataset.url;
    var crear = (select.dataset.crear || "").split(",").filter(Boolean);
    var etiqueta = select.dataset.etiqueta || "";

    var caja = document.createElement("div");
    caja.className = "persona";

    var boton = document.createElement("button");
    boton.type = "button";
    boton.className = "persona-slot";
    boton.setAttribute("aria-haspopup", "dialog");
    boton.setAttribute("aria-label", etiqueta ? "Elegir " + etiqueta : "Elegir persona");
    boton.innerHTML =
      '<span class="persona-nombre" data-persona-nombre></span>' +
      '<span class="persona-mas" aria-hidden="true">+</span>';

    var nombre = boton.querySelector("[data-persona-nombre]");
    function pintar() {
      var texto = textoDe(select, crear);
      nombre.textContent = texto || "Sin asignar";
      caja.classList.toggle("persona-vacia", !texto);
    }

    select.parentNode.insertBefore(caja, select);
    caja.appendChild(select);
    caja.appendChild(boton);
    select.classList.add("persona-select");
    pintar();

    boton.addEventListener("click", function () {
      abrir(select, url, crear, etiqueta, pintar);
    });
  }

  function iniciar(raiz) {
    raiz.querySelectorAll("select[data-persona-picker]").forEach(mejorar);
  }

  function arrancar() {
    iniciar(document);
    var modal = document.querySelector("[data-modal-dialog]");
    if (modal && window.MutationObserver) {
      new MutationObserver(function () {
        iniciar(modal);
      }).observe(modal, { childList: true });
    }
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", arrancar);
  } else {
    arrancar();
  }
})();
