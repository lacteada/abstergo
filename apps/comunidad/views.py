from apps.common.vistas_base import (
    AltaBase,
    BorradoBase,
    ConsultaBase,
    DesactivarBase,
    EdicionBase,
    ListadoBase,
    ReactivarBase,
)
from apps.comunidad.forms import OrganizacionForm
from apps.comunidad.models import Organizacion


class Listado(ListadoBase):
    model = Organizacion
    template_name = "comunidad/organizaciones_lista.html"
    titulo = "Organizaciones comunitarias"
    subtitulo = "Juntas de vecinos y agrupaciones del registro OROC."
    seccion = "organizaciones"
    etiqueta_nueva = "Nueva organización"
    busqueda = ("referencia", "codigo", "nombre", "domicilio_legal", "registro_pj")
    relacionadas = ("territorio",)
    exportar_nombre = "organizaciones"
    exportar_columnas = (
        ("Código", "referencia"),
        ("Nombre", "nombre"),
        ("Domicilio legal", "domicilio_legal"),
        ("Territorio", "territorio.nombre"),
        ("Tipo", "get_tipo_display"),
        ("Subtipo", "get_subtipo_display"),
        ("Situación", "get_situacion_display"),
        ("Verificación", "get_verificacion_display"),
        ("Socios activos", "socios_activos"),
        ("Constitución", "fecha_constitucion"),
        ("Registro P.J.", "registro_pj"),
        ("Inscripción", "fecha_inscripcion"),
        ("Registro directorio", "registro_dir"),
        ("Estado", "get_estado_display"),
    )
    url_nueva = "comunidad:organizaciones_nueva"
    url_listado = "comunidad:organizaciones"


class Alta(AltaBase):
    model = Organizacion
    form_class = OrganizacionForm
    titulo = "Nueva organización"
    seccion = "organizaciones"
    url_listado = "comunidad:organizaciones"


class Edicion(EdicionBase):
    model = Organizacion
    form_class = OrganizacionForm
    titulo = "Editar organización"
    seccion = "organizaciones"
    url_listado = "comunidad:organizaciones"


class Borrado(BorradoBase):
    model = Organizacion
    titulo = "Eliminar organización"
    seccion = "organizaciones"
    url_listado = "comunidad:organizaciones"


class Desactivar(DesactivarBase):
    model = Organizacion
    titulo = "Organización"
    seccion = "organizaciones"
    url_listado = "comunidad:organizaciones"


class Reactivar(ReactivarBase):
    model = Organizacion
    titulo = "Organización"
    seccion = "organizaciones"
    url_listado = "comunidad:organizaciones"


class Consulta(ConsultaBase):
    model = Organizacion
    titulo = "Consultar organización"
    seccion = "organizaciones"
    url_listado = "comunidad:organizaciones"
    consulta_campos = (
        ("Código", "referencia"),
        ("Clave", "codigo"),
        ("Nombre", "nombre"),
        ("Domicilio legal", "domicilio_legal"),
        ("Territorio", "territorio.nombre"),
        ("Tipo", "get_tipo_display"),
        ("Subtipo", "get_subtipo_display"),
        ("Situación", "get_situacion_display"),
        ("Verificación", "get_verificacion_display"),
        ("Socios activos", "socios_activos"),
        ("Fecha de constitución", "fecha_constitucion"),
        ("N° registro P.J.", "registro_pj"),
        ("Fecha de inscripción", "fecha_inscripcion"),
        ("N° registro directorio", "registro_dir"),
        ("Estado", "get_estado_display"),
    )
