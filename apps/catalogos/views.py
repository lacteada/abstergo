from apps.catalogos.forms import MetaForm, SubAtencionForm, TipoAtencionForm
from apps.catalogos.models import Meta, SubAtencion, TipoAtencion
from apps.common.vistas_base import AltaBase, BorradoBase, EdicionBase, ListadoBase


# ------------------------------------------------------------------- Metas
class MetasListado(ListadoBase):
    model = Meta
    template_name = "catalogos/metas_lista.html"
    titulo = "Metas"
    seccion = "metas"
    etiqueta_nueva = "Nueva meta"
    busqueda = ("nombre", "descripcion", "delegacion__nombre")
    relacionadas = ("delegacion",)
    exportar_nombre = "metas"
    exportar_columnas = (
        ("Nombre", "nombre"),
        ("Delegación", "delegacion.nombre"),
        ("Descripción", "descripcion"),
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


# -------------------------------------------------------- Tipo de Atención
class TiposListado(ListadoBase):
    model = TipoAtencion
    template_name = "catalogos/tipos_lista.html"
    titulo = "Tipo de Atención"
    seccion = "tipos"
    etiqueta_nueva = "Nuevo tipo de atención"
    busqueda = ("nombre", "descripcion")
    exportar_nombre = "tipos_atencion"
    exportar_columnas = (
        ("Nombre", "nombre"),
        ("Descripción", "descripcion"),
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


# ------------------------------------------------------------ Sub Atención
class SubAtencionesListado(ListadoBase):
    model = SubAtencion
    template_name = "catalogos/subatenciones_lista.html"
    titulo = "Sub Atención"
    seccion = "subatenciones"
    etiqueta_nueva = "Nueva sub atención"
    busqueda = ("nombre", "tipo_atencion__nombre")
    relacionadas = ("tipo_atencion",)
    exportar_nombre = "sub_atenciones"
    exportar_columnas = (
        ("Nombre", "nombre"),
        ("Tipo de Atención", "tipo_atencion.nombre"),
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
