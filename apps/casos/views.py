"""Mantenedores de los casos sociales y sus gestiones.

Cada recurso declara un mixin con su modelo, formulario y rutas; las acciones
del CRUD se arman encima y comparten el comportamiento de `vistas_base.py`.
"""

from apps.casos.forms import CasoSocialForm, GestionCasoForm, LlamadaForm
from apps.casos.models import CasoSocial, GestionCaso, Llamada
from apps.common.vistas_base import (
    AltaBase,
    BorradoBase,
    ConsultaBase,
    DesactivarBase,
    EdicionBase,
    ListadoBase,
    ReactivarBase,
)


# --------------------------------------------------------------------- Casos
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
        ("Responsable", "responsable.get_full_name"),
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


# ----------------------------------------------------------------- Gestiones
class _Gestiones:
    model = GestionCaso
    form_class = GestionCasoForm
    titulo = "Gestiones del caso"
    seccion = "casos"
    url_listado = "casos:gestiones"


class GestionesListado(_Gestiones, ListadoBase):
    template_name = "casos/gestiones_lista.html"
    etiqueta_nueva = "Nueva gestión"
    busqueda = ("referencia", "detalle", "caso__referencia", "caso__vecino__nombre")
    relacionadas = ("caso",)
    exportar_nombre = "gestiones_caso"
    exportar_columnas = (
        ("Código", "referencia"),
        ("Caso", "caso.referencia"),
        ("Fecha", "fecha"),
        ("Tipo", "get_tipo_display"),
        ("Hito", "hito"),
        ("Plazo", "plazo"),
    )
    url_nueva = "casos:gestiones_nueva"


class GestionesAlta(_Gestiones, AltaBase):
    titulo = "Nueva gestión"


class GestionesEdicion(_Gestiones, EdicionBase):
    titulo = "Editar gestión"


class GestionesBorrado(_Gestiones, BorradoBase):
    titulo = "Eliminar gestión"


class GestionesDesactivar(_Gestiones, DesactivarBase):
    pass


class GestionesReactivar(_Gestiones, ReactivarBase):
    pass


class GestionesConsulta(_Gestiones, ConsultaBase):
    titulo = "Consultar gestión"
    consulta_campos = (
        ("Código", "referencia"),
        ("Caso", "caso.referencia"),
        ("Fecha", "fecha"),
        ("Tipo", "get_tipo_display"),
        ("Hito", "hito"),
        ("Plazo", "plazo"),
        ("Detalle", "detalle"),
    )


# ---------------------------------------------------------------- Llamadas
class _Llamadas:
    model = Llamada
    form_class = LlamadaForm
    titulo = "Llamadas preventivas"
    seccion = "casos"
    url_listado = "casos:llamadas"


class LlamadasListado(_Llamadas, ListadoBase):
    template_name = "casos/llamadas_lista.html"
    etiqueta_nueva = "Nueva llamada"
    busqueda = ("referencia", "motivo", "vecino__nombre")
    relacionadas = ("vecino", "responsable")
    exportar_nombre = "llamadas_preventivas"
    exportar_columnas = (
        ("Código", "referencia"),
        ("Vecino", "vecino.nombre"),
        ("Motivo", "motivo"),
        ("Programada", "fecha_programada"),
        ("Estado", "get_estado_display"),
    )
    url_nueva = "casos:llamadas_nueva"


class LlamadasAlta(_Llamadas, AltaBase):
    titulo = "Nueva llamada"


class LlamadasEdicion(_Llamadas, EdicionBase):
    titulo = "Editar llamada"


class LlamadasBorrado(_Llamadas, BorradoBase):
    titulo = "Eliminar llamada"


class LlamadasDesactivar(_Llamadas, DesactivarBase):
    pass


class LlamadasReactivar(_Llamadas, ReactivarBase):
    pass


class LlamadasConsulta(_Llamadas, ConsultaBase):
    titulo = "Consultar llamada"
    consulta_campos = (
        ("Código", "referencia"),
        ("Vecino", "vecino.nombre"),
        ("Motivo", "motivo"),
        ("Programada", "fecha_programada"),
        ("Estado", "get_estado_display"),
        ("Responsable", "responsable.get_full_name"),
        ("Resultado", "resultado"),
    )
