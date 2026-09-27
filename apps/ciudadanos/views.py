from apps.ciudadanos.forms import VecinoForm
from apps.ciudadanos.models import Vecino
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
    url_nueva = "ciudadanos:vecinos_nueva"
    url_listado = "ciudadanos:vecinos"


class Alta(AltaBase):
    model = Vecino
    form_class = VecinoForm
    titulo = "Nuevo vecino"
    seccion = "vecinos"
    url_listado = "ciudadanos:vecinos"


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
