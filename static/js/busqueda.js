/* Búsqueda en tiempo real de los listados.

   Pide la misma dirección del listado con ?q=, se queda con las filas de la
   respuesta y las cambia en la tabla. No recarga la página, así que el foco
   se queda en el buscador mientras escribes.

   El formulario sigue funcionando sin JavaScript: si esto no corre, Enter en
   el buscador hace la carga completa de siempre.
*/
function iniciarBusqueda() {
  const entrada = document.querySelector("[data-busqueda]");
  if (!entrada) return;

  const filas = document.querySelector("[data-filas]");
  const pie = document.querySelector("[data-pie]");
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
      if (nuevoPie) pie.innerHTML = nuevoPie.innerHTML;
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
