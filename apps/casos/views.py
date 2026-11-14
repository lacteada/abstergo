"""Mantenedor de los casos sociales (la atención es su gestión).

Las gestiones del caso son las atenciones del vecino; este módulo solo
administra el caso.
"""

from apps.casos.forms import CasoSocialForm
from apps.casos.models import CasoSocial
from apps.common.vistas_base import (
    AltaBase,
    BorradoBase,
    ConsultaBase,
    DesactivarBase,
    EdicionBase,
    ListadoBase,
    ReactivarBase,
)


class _Casos:
    model = CasoSocial
    form_class = CasoSocialForm
    titulo = "Casos sociales"
    seccion = "casos"
    url_listado = "casos:casos"


class CasosListado(_Casos, ListadoBase):
    template_name = "casos/casos_lista.html"
    etiqueta_nueva = "Nuevo caso"
    busqueda = ("referencia", "motivo", "vecino__nombre", "responsable__first_name")
    relacionadas = ("vecino", "responsable")
    exportar_nombre = "casos_sociales"
    exportar_columnas = (
        ("Código", "referencia"),
        ("Vecino", "vecino.nombre"),
        ("Motivo", "motivo"),
        ("Estado", "get_estado_display"),
        ("Apertura", "fecha_apertura"),
        ("Atenciones", "atenciones.count"),
    )
    url_nueva = "casos:casos_nueva"


class CasosAlta(_Casos, AltaBase):
    titulo = "Nuevo caso"


class CasosEdicion(_Casos, EdicionBase):
    titulo = "Editar caso"


class CasosBorrado(_Casos, BorradoBase):
    titulo = "Eliminar caso"


class CasosDesactivar(_Casos, DesactivarBase):
    pass


class CasosReactivar(_Casos, ReactivarBase):
    pass


class CasosConsulta(_Casos, ConsultaBase):
    titulo = "Consultar caso"
    consulta_campos = (
        ("Código", "referencia"),
        ("Vecino", "vecino.nombre"),
        ("Motivo", "motivo"),
        ("Estado", "get_estado_display"),
        ("Apertura", "fecha_apertura"),
        ("Responsable", "responsable.get_full_name"),
        ("Reingreso", "reingreso"),
        ("Caso anterior", "caso_anterior.referencia"),
        ("Observaciones", "observaciones"),
    )
