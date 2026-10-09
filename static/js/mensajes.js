/* Mensajes y confirmaciones con SweetAlert2.

   - Las messages de Django se muestran como avisos tipo toast.
   - Los enlaces de baja ([data-eliminar]) piden confirmación y envían el POST.
   Si SweetAlert no carga, los enlaces siguen funcionando como enlaces normales.

   Los eventos van por delegación: las filas que reemplazan la búsqueda o el
   modal siguen funcionando sin volver a enganchar listeners.
   `window.Mensajes.avisar` lo reutiliza modal.js para el toast tras guardar.
*/
(function () {
  function iconoDe(nivel) {
    if (nivel.indexOf("error") !== -1) return "error";
    if (nivel.indexOf("warning") !== -1) return "warning";
    if (nivel.indexOf("success") !== -1) return "success";
    return "info";
  }

  function avisar(nivel, texto) {
    if (!window.Swal) return;
    Swal.fire({
      toast: true,
      position: "top-end",
      icon: iconoDe(nivel || "info"),
      title: texto,
      showConfirmButton: false,
      timer: 3200,
      timerProgressBar: true,
    });
  }

  window.Mensajes = { avisar: avisar };

  function avisos() {
    const contenedor = document.querySelector("[data-mensajes]");
    if (!contenedor) return;
    contenedor.querySelectorAll("[data-nivel]").forEach(function (nodo) {
      avisar(nodo.dataset.nivel, nodo.textContent.trim());
    });
  }

  function confirmaciones() {
    document.addEventListener("click", function (evento) {
      const enlace = evento.target.closest("[data-eliminar], a.accion.peligro");
      const formulario = document.getElementById("form-baja");
      if (!enlace || !formulario || !window.Swal) return; // sigue el enlace normal
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
