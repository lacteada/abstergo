/* Dependencia Tipo de Atención → Sub Atención.

   La segunda lista muestra solo las sub atenciones del tipo elegido y, si el
   tipo cambia, la sub atención deja de ser válida y se limpia. El servidor
   aplica la misma regla (AtencionForm.clean), así que esto es la comodidad,
   no el control.

   Engancha por delegación y sobre el modal, que reemplaza su contenido: el
   formulario puede aparecer después de cargar la página.
*/
(function () {
  const TIPO = "#id_tipo_atencion";
  const SUB = "#id_sub_atencion";

  function nuevaOpcion(valor, texto) {
    const opcion = document.createElement("option");
    opcion.value = valor;
    opcion.textContent = texto;
    return opcion;
  }

  function aplicar(sub, patron) {
    const previo = sub.value;
    sub.innerHTML = "";
    sub.appendChild(nuevaOpcion("", "---------"));
    (sub._todas || []).forEach(function (opcion) {
      if (!opcion.value) return;
      if (patron && opcion.tipo !== patron) return;
      sub.appendChild(nuevaOpcion(opcion.value, opcion.texto));
    });
    const disponible = Array.from(sub.options).some(function (opcion) {
      return opcion.value === previo;
    });
    sub.value = disponible ? previo : "";
  }

  function enganchar(raiz) {
    const tipo = raiz.querySelector(TIPO);
    const sub = raiz.querySelector(SUB);
    if (!tipo || !sub || tipo.dataset.dependiente === "1") return;
    tipo.dataset.dependiente = "1";
    // Catálogo completo la primera vez; después se filtra sobre esto.
    sub._todas = Array.from(sub.options).map(function (opcion) {
      return {
        value: opcion.value,
        texto: opcion.textContent,
        tipo: opcion.dataset.tipo || "",
      };
    });
    tipo.addEventListener("change", function () {
      aplicar(sub, tipo.value);
    });
    aplicar(sub, tipo.value);
  }

  function iniciar() {
    enganchar(document);
    const dialogo = document.querySelector("[data-modal-dialog]");
    if (dialogo && window.MutationObserver) {
      // El modal reemplaza su contenido al abrir; hay que reenganchar.
      new MutationObserver(function () {
        enganchar(dialogo);
      }).observe(dialogo, { childList: true });
    }
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", iniciar);
  } else {
    iniciar();
  }
})();
