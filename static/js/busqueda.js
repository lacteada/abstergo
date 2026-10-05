/* Búsqueda en tiempo real de los listados.

   Pide la misma dirección del listado con ?q=, se queda con las filas, el
   contador y el paginador de la respuesta, y los cambia en la tabla. No
   recarga la página, así que el foco se queda en el buscador.

   El formulario sigue funcionando sin JavaScript: si esto no corre, Enter en
   el buscador hace la carga completa de siempre.
*/
function iniciarBusqueda() {
  const entrada = document.querySelector("[data-busqueda]");
  if (!entrada) return;

  const filas = document.querySelector("[data-filas]");
  const pie = document.querySelector("[data-pie]");
  const paginacion = document.querySelector("[data-paginacion]");
  let temporizador = null;

  async function actualizar() {
    const destino =
      entrada.dataset.url + "?q=" + encodeURIComponent(entrada.value.trim());
    try {
      const respuesta = await fetch(destino);
      if (!respuesta.ok) return;
      const documento = new DOMParser().parseFromString(
        await respuesta.text(),
        "text/html"
      );
      const nuevasFilas = documento.querySelector("[data-filas]");
      if (nuevasFilas) filas.innerHTML = nuevasFilas.innerHTML;
      const nuevoPie = documento.querySelector("[data-pie]");
      if (nuevoPie && pie) pie.innerHTML = nuevoPie.innerHTML;
      const nuevaPaginacion = documento.querySelector("[data-paginacion]");
      if (paginacion) {
        paginacion.innerHTML = nuevaPaginacion ? nuevaPaginacion.innerHTML : "";
      }
    } catch (error) {
      // Si falla la red se deja lo que ya estaba en pantalla.
    }
  }

  entrada.addEventListener("input", () => {
    clearTimeout(temporizador);
    temporizador = setTimeout(actualizar, 250);
  });
}

if (document.readyState === "loading") {
  document.addEventListener("DOMContentLoaded", iniciarBusqueda);
} else {
  iniciarBusqueda();
}
