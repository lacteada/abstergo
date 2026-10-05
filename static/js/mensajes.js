/* Mensajes y confirmaciones con SweetAlert2.

   - Las messages de Django se muestran como avisos tipo toast.
   - Los enlaces de baja (.accion.peligro) piden confirmación y envían el POST.
   Si SweetAlert no carga, los enlaces siguen funcionando como enlaces normales.
*/
(function () {
  function avisos() {
    const contenedor = document.querySelector("[data-mensajes]");
    if (!contenedor || !window.Swal) return;
    contenedor.querySelectorAll("[data-nivel]").forEach(function (nodo) {
      const nivel = nodo.dataset.nivel || "info";
      let icono = "info";
      if (nivel.indexOf("error") !== -1) icono = "error";
      else if (nivel.indexOf("warning") !== -1) icono = "warning";
      else if (nivel.indexOf("success") !== -1) icono = "success";
      Swal.fire({
        toast: true,
        position: "top-end",
        icon: icono,
        title: nodo.textContent.trim(),
        showConfirmButton: false,
        timer: 3200,
        timerProgressBar: true,
      });
    });
  }

  function confirmaciones() {
    const formulario = document.getElementById("form-baja");
    document.querySelectorAll("a.accion.peligro").forEach(function (enlace) {
      enlace.addEventListener("click", function (evento) {
        if (!window.Swal || !formulario) return; // sigue el enlace normal
        evento.preventDefault();
        Swal.fire({
          icon: "warning",
          title: "¿Confirmas dar de baja?",
          text: "El registro se retira del sistema.",
          showCancelButton: true,
          confirmButtonText: "Eliminar",
          cancelButtonText: "Cancelar",
          confirmButtonColor: "#8B1D19",
          cancelButtonColor: "#5b6169",
        }).then(function (resultado) {
          if (resultado.isConfirmed) {
            formulario.action = enlace.getAttribute("href");
            formulario.submit();
          }
        });
      });
    });
  }

  function iniciar() {
    avisos();
    confirmaciones();
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", iniciar);
  } else {
    iniciar();
  }
})();
