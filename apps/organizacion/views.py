from apps.common.vistas_base import (
    AltaBase,
    BorradoBase,
    ConsultaBase,
    DesactivarBase,
    EdicionBase,
    ListadoBase,
    ReactivarBase,
)
from apps.organizacion.forms import CargoForm, DelegacionForm
from apps.organizacion.models import Cargo, Delegacion


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


class Desactivar(DesactivarBase):
    model = Delegacion
    titulo = "Delegación"
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


# ------------------------------------------------------------------ Cargos
class CargosListado(ListadoBase):
    model = Cargo
    template_name = "organizacion/cargos_lista.html"
    titulo = "Cargos"
    seccion = "cargos"
    etiqueta_nueva = "Nuevo cargo"
    busqueda = ("referencia", "codigo", "nombre", "descripcion")
    exportar_nombre = "cargos"
    exportar_columnas = (
        ("Código", "codigo"),
        ("Nombre", "nombre"),
        ("Descripción", "descripcion"),
    )
    url_nueva = "organizacion:cargos_nueva"
    url_listado = "organizacion:cargos"


class CargosAlta(AltaBase):
    model = Cargo
    form_class = CargoForm
    titulo = "Nuevo cargo"
    seccion = "cargos"
    url_listado = "organizacion:cargos"


class CargosEdicion(EdicionBase):
    model = Cargo
    form_class = CargoForm
    titulo = "Editar cargo"
    seccion = "cargos"
    url_listado = "organizacion:cargos"


class CargosBorrado(BorradoBase):
    model = Cargo
    titulo = "Eliminar cargo"
    seccion = "cargos"
    url_listado = "organizacion:cargos"


class CargosDesactivar(DesactivarBase):
    model = Cargo
    titulo = "Cargo"
    seccion = "cargos"
    url_listado = "organizacion:cargos"


class CargosReactivar(ReactivarBase):
    model = Cargo
    titulo = "Cargo"
    seccion = "cargos"
    url_listado = "organizacion:cargos"


class CargosConsulta(ConsultaBase):
    model = Cargo
    titulo = "Consultar cargo"
    seccion = "cargos"
    url_listado = "organizacion:cargos"
    consulta_campos = (
        ("Código", "referencia"),
        ("Clave", "codigo"),
        ("Nombre", "nombre"),
        ("Descripción", "descripcion"),
    )
