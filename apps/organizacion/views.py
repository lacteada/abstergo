from apps.common.vistas_base import (
    AltaBase,
    BorradoBase,
    ConsultaBase,
    EdicionBase,
    ListadoBase,
    ReactivarBase,
)
from apps.organizacion.forms import DelegacionForm
from apps.organizacion.models import Delegacion


class Listado(ListadoBase):
    model = Delegacion
    template_name = "organizacion/delegaciones_lista.html"
    titulo = "Delegaciones Municipales"
    seccion = "delegaciones"
    etiqueta_nueva = "Nueva delegación"
    busqueda = ("referencia", "codigo", "nombre", "comuna", "responsable__first_name")
    relacionadas = ("responsable",)
    campo_delegacion = "pk"
    exportar_nombre = "delegaciones"
    exportar_columnas = (
        ("Código", "codigo"),
        ("Nombre", "nombre"),
        ("Dirección", "direccion"),
        ("Comuna", "comuna"),
        ("Responsable", "responsable.get_full_name"),
        ("Estado", "get_estado_display"),
    )
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


class Reactivar(ReactivarBase):
    model = Delegacion
    titulo = "Delegación"
    seccion = "delegaciones"
    url_listado = "organizacion:delegaciones"


class Consulta(ConsultaBase):
    model = Delegacion
    titulo = "Consultar delegación"
    seccion = "delegaciones"
    url_listado = "organizacion:delegaciones"
    consulta_campos = (
        ("Código", "referencia"),
        ("Clave", "codigo"),
        ("Nombre", "nombre"),
        ("Dirección", "direccion"),
        ("Comuna", "comuna"),
        ("Responsable", "responsable.get_full_name"),
        ("Estado", "get_estado_display"),
    )
