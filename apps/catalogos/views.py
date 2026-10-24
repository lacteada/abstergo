from apps.catalogos.forms import MetaForm, SubAtencionForm, TipoAtencionForm
from apps.catalogos.models import Meta, SubAtencion, TipoAtencion
from apps.common.vistas_base import (
    AltaBase,
    BorradoBase,
    ConsultaBase,
    DesactivarBase,
    EdicionBase,
    ListadoBase,
    ReactivarBase,
)


# ------------------------------------------------------------------- Metas
class MetasListado(ListadoBase):
    model = Meta
    template_name = "catalogos/metas_lista.html"
    titulo = "Metas"
    seccion = "metas"
    etiqueta_nueva = "Nueva meta"
    busqueda = ("referencia", "codigo", "nombre", "descripcion", "delegacion__nombre")
    relacionadas = ("delegacion",)
    campo_delegacion = "delegacion"
    exportar_nombre = "metas"
    exportar_columnas = (
        ("Código", "codigo"),
        ("Nombre", "nombre"),
        ("Delegación", "delegacion.nombre"),
        ("Descripción", "descripcion"),
        ("Estado", "get_estado_display"),
    )
    url_nueva = "catalogos:metas_nueva"
    url_listado = "catalogos:metas"


class MetasAlta(AltaBase):
    model = Meta
    form_class = MetaForm
    titulo = "Nueva meta"
    seccion = "metas"
    url_listado = "catalogos:metas"


class MetasEdicion(EdicionBase):
    model = Meta
    form_class = MetaForm
    titulo = "Editar meta"
    seccion = "metas"
    url_listado = "catalogos:metas"


class MetasBorrado(BorradoBase):
    model = Meta
    titulo = "Eliminar meta"
    seccion = "metas"
    url_listado = "catalogos:metas"


class MetasDesactivar(DesactivarBase):
    model = Meta
    titulo = "Meta"
    seccion = "metas"
    url_listado = "catalogos:metas"


class MetasReactivar(ReactivarBase):
    model = Meta
    titulo = "Meta"
    seccion = "metas"
    url_listado = "catalogos:metas"


class MetasConsulta(ConsultaBase):
    model = Meta
    titulo = "Consultar meta"
    seccion = "metas"
    url_listado = "catalogos:metas"
    consulta_campos = (
        ("Código", "referencia"),
        ("Clave", "codigo"),
        ("Nombre", "nombre"),
        ("Delegación", "delegacion.nombre"),
        ("Descripción", "descripcion"),
        ("Estado", "get_estado_display"),
    )


# -------------------------------------------------------- Tipo de Atención
class TiposListado(ListadoBase):
    model = TipoAtencion
    template_name = "catalogos/tipos_lista.html"
    titulo = "Tipo de Atención"
    seccion = "tipos"
    etiqueta_nueva = "Nuevo tipo de atención"
    busqueda = ("referencia", "codigo", "nombre", "descripcion")
    exportar_nombre = "tipos_atencion"
    exportar_columnas = (
        ("Código", "codigo"),
        ("Nombre", "nombre"),
        ("Descripción", "descripcion"),
        ("Estado", "get_estado_display"),
    )
    url_nueva = "catalogos:tipos_nueva"
    url_listado = "catalogos:tipos"


class TiposAlta(AltaBase):
    model = TipoAtencion
    form_class = TipoAtencionForm
    titulo = "Nuevo tipo de atención"
    seccion = "tipos"
    url_listado = "catalogos:tipos"


class TiposEdicion(EdicionBase):
    model = TipoAtencion
    form_class = TipoAtencionForm
    titulo = "Editar tipo de atención"
    seccion = "tipos"
    url_listado = "catalogos:tipos"


class TiposBorrado(BorradoBase):
    model = TipoAtencion
    titulo = "Eliminar tipo de atención"
    seccion = "tipos"
    url_listado = "catalogos:tipos"


class TiposDesactivar(DesactivarBase):
    model = TipoAtencion
    titulo = "Tipo de atención"
    seccion = "tipos"
    url_listado = "catalogos:tipos"


class TiposReactivar(ReactivarBase):
    model = TipoAtencion
    titulo = "Tipo de atención"
    seccion = "tipos"
    url_listado = "catalogos:tipos"


class TiposConsulta(ConsultaBase):
    model = TipoAtencion
    titulo = "Consultar tipo de atención"
    seccion = "tipos"
    url_listado = "catalogos:tipos"
    consulta_campos = (
        ("Código", "referencia"),
        ("Clave", "codigo"),
        ("Nombre", "nombre"),
        ("Descripción", "descripcion"),
        ("Estado", "get_estado_display"),
    )


# ------------------------------------------------------------ Sub Atención
class SubAtencionesListado(ListadoBase):
    model = SubAtencion
    template_name = "catalogos/subatenciones_lista.html"
    titulo = "Sub Atención"
    seccion = "subatenciones"
    etiqueta_nueva = "Nueva sub atención"
    busqueda = ("referencia", "codigo", "nombre", "tipo_atencion__nombre")
    relacionadas = ("tipo_atencion",)
    exportar_nombre = "sub_atenciones"
    exportar_columnas = (
        ("Código", "codigo"),
        ("Nombre", "nombre"),
        ("Tipo de Atención", "tipo_atencion.nombre"),
        ("Estado", "get_estado_display"),
    )
    url_nueva = "catalogos:subatenciones_nueva"
    url_listado = "catalogos:subatenciones"


class SubAtencionesAlta(AltaBase):
    model = SubAtencion
    form_class = SubAtencionForm
    titulo = "Nueva sub atención"
    seccion = "subatenciones"
    url_listado = "catalogos:subatenciones"


class SubAtencionesEdicion(EdicionBase):
    model = SubAtencion
    form_class = SubAtencionForm
    titulo = "Editar sub atención"
    seccion = "subatenciones"
    url_listado = "catalogos:subatenciones"


class SubAtencionesBorrado(BorradoBase):
    model = SubAtencion
    titulo = "Eliminar sub atención"
    seccion = "subatenciones"
    url_listado = "catalogos:subatenciones"


class SubAtencionesDesactivar(DesactivarBase):
    model = SubAtencion
    titulo = "Sub atención"
    seccion = "subatenciones"
    url_listado = "catalogos:subatenciones"


class SubAtencionesReactivar(ReactivarBase):
    model = SubAtencion
    titulo = "Sub atención"
    seccion = "subatenciones"
    url_listado = "catalogos:subatenciones"


class SubAtencionesConsulta(ConsultaBase):
    model = SubAtencion
    titulo = "Consultar sub atención"
    seccion = "subatenciones"
    url_listado = "catalogos:subatenciones"
    consulta_campos = (
        ("Código", "referencia"),
        ("Clave", "codigo"),
        ("Nombre", "nombre"),
        ("Tipo de Atención", "tipo_atencion.nombre"),
        ("Estado", "get_estado_display"),
    )
