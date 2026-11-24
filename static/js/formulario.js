/* Estado de envío: al mandar un formulario, el botón de guardar se desactiva y
   avisa que está trabajando, para que no se envíe dos veces. */
(function () {
  "use strict";

  document.addEventListener(
    "submit",
    function (evento) {
      var formulario = evento.target;
      if (
        !formulario.classList ||
        !formulario.classList.contains("formulario")
      ) {
        return;
      }
      var boton = formulario.querySelector('button[type="submit"]');
      if (boton) {
        boton.disabled = true;
        boton.classList.add("enviando");
        boton.setAttribute("aria-busy", "true");
      }
    },
    true
  );
})();
