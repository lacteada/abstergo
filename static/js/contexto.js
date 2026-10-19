/* Cambio de delegación activa.

   El selector de la cabecera recarga el contexto en el servidor (los listados,
   filtros y exportaciones dependen de él). Si hay un formulario abierto con
   cambios sin guardar, se advierte antes de cambiar y, si el usuario cancela,
   el selector vuelve a su valor anterior.

   Sin JavaScript, el formulario del selector se envía igual: la degradación es
   automática.
*/
(function () {
  const formulario = document.querySelector("[data-cambiar-delegacion]");
  if (!formulario) return;

  const selector = formulario.querySelector("select");
  if (!selector) return;

  let valorPrevio = selector.value;
  let hayCambios = false;

  function marcarCambios() {
    hayCambios = true;
  }

  document.addEventListener("input", function (evento) {
    if (evento.target.closest(".formulario, .auth-form, form[method='post']")) {
      marcarCambios();
    }
  });

  selector.addEventListener("change", function () {
    if (!hayCambios || !window.Swal) {
      formulario.submit();
      return;
    }
    Swal.fire({
      icon: "warning",
      title: "Hay cambios sin guardar",
      text: "Si cambias de delegación se perderán los datos del formulario.",
      showCancelButton: true,
      confirmButtonText: "Cambiar de todos modos",
      cancelButtonText: "Seguir editando",
      confirmButtonColor: "#8B1D19",
      cancelButtonColor: "#5b6169",
    }).then(function (resultado) {
      if (resultado.isConfirmed) {
        formulario.submit();
      } else {
        selector.value = valorPrevio;
      }
    });
  });
})();
