from apps.organizacion.forms import DelegacionForm
from apps.organizacion.models import Delegacion
from apps.common.vistas_base import AltaBase, BorradoBase, EdicionBase, ListadoBase


class Listado(ListadoBase):
    model = Delegacion
    template_name = "organizacion/delegaciones_lista.html"
    titulo = "Delegaciones Municipales"
    seccion = "delegaciones"
    etiqueta_nueva = "Nueva delegación"
    busqueda = ("codigo", "nombre", "comuna")
    url_nueva = "organizacion:delegaciones_nueva"
    url_listado = "organizacion:delegaciones"


class Alta(AltaBase):
    model = Delegacion
    form_class = DelegacionForm
    titulo = "Nueva delegación"
    seccion = "delegaciones"
    url_listado = "organizacion:delegaciones"


class Edicion(EdicionBase):
    model = Delegacion
    form_class = DelegacionForm
    titulo = "Editar delegación"
    seccion = "delegaciones"
    url_listado = "organizacion:delegaciones"


class Borrado(BorradoBase):
    model = Delegacion
    titulo = "Eliminar delegación"
    seccion = "delegaciones"
    url_listado = "organizacion:delegaciones"
