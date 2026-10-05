from apps.ciudadanos.forms import VecinoForm
from apps.ciudadanos.models import Vecino
from apps.common.validators import normalizar_rut
from apps.common.vistas_base import AltaBase, BorradoBase, EdicionBase, ListadoBase


class Listado(ListadoBase):
    model = Vecino
    template_name = "ciudadanos/vecinos_lista.html"
    titulo = "Vecinos"
    subtitulo = "CRUD de vecinos"
    seccion = "vecinos"
    etiqueta_nueva = "Nuevo vecino"
    busqueda = (
        "nombre",
        "rut",
        "direccion",
        "telefono",
        "territorio__nombre",
        "tipo_gestion",
    )
    relacionadas = ("territorio",)
    auditar_lectura = True
    exportar_nombre = "vecinos"
    exportar_columnas = (
        ("Nombre", "nombre"),
        ("RUT", "rut"),
        ("Dirección", "direccion"),
        ("Teléfono", "telefono"),
        ("Territorio", "territorio.nombre"),
        ("Tipo de Gestión", "tipo_gestion"),
        ("Estado", "get_estado_display"),
    )
    url_nueva = "ciudadanos:vecinos_nueva"
    url_listado = "ciudadanos:vecinos"


class Alta(AltaBase):
    model = Vecino
    form_class = VecinoForm
    titulo = "Nuevo vecino"
    seccion = "vecinos"
    url_listado = "ciudadanos:vecinos"

    def get_initial(self):
        # Permite llegar desde "Crear Atención" con el RUT y el nombre puestos.
        inicial = super().get_initial()
        rut = self.request.GET.get("rut")
        nombre = self.request.GET.get("nombre")
        if rut:
            inicial["rut"] = normalizar_rut(rut)
        if nombre:
            inicial["nombre"] = nombre
        return inicial


class Edicion(EdicionBase):
    model = Vecino
    form_class = VecinoForm
    titulo = "Editar vecino"
    seccion = "vecinos"
    url_listado = "ciudadanos:vecinos"


class Borrado(BorradoBase):
    model = Vecino
    titulo = "Eliminar vecino"
    seccion = "vecinos"
    url_listado = "ciudadanos:vecinos"
