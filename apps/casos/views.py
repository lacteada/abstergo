"""Mantenedor de los casos sociales (la atención es su gestión).

Las gestiones del caso son las atenciones del vecino; este módulo solo
administra el caso.
"""

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404, redirect
from django.utils import timezone
from django.views import View

from apps.casos.forms import CasoSocialForm, LlamadaForm
from apps.casos.models import CasoSocial, Llamada
from apps.common.delegaciones import acotar, campo_delegacion_de
from apps.common.vistas_base import (
    AltaBase,
    BorradoBase,
    ConsultaBase,
    DesactivarBase,
    EdicionBase,
    ListadoBase,
    PermisoRequeridoMixin,
    ReactivarBase,
)
from apps.cumplimiento.auditoria import registrar


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


# ----------------------------------------------- Llamadas preventivas (RF-050)
class _Llamadas:
    model = Llamada
    form_class = LlamadaForm
    titulo = "Llamadas preventivas"
    seccion = "casos"
    url_listado = "casos:llamadas"


class LlamadasListado(_Llamadas, ListadoBase):
    template_name = "casos/llamadas_lista.html"
    etiqueta_nueva = "Nueva llamada"
    busqueda = ("referencia", "motivo", "vecino__nombre", "vecino__rut")
    relacionadas = ("vecino", "atencion")
    exportar_nombre = "llamadas"
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


class LlamadasConsulta(_Llamadas, ConsultaBase):
    consulta_campos = (
        ("Código", "referencia"),
        ("Vecino", "vecino.nombre"),
        ("Atención", "atencion.referencia"),
        ("Motivo", "motivo"),
        ("Programada", "fecha_programada"),
        ("Estado", "get_estado_display"),
        ("Realizada por", "realizada_por.get_full_name"),
    )


class LlamadasCerrar(LoginRequiredMixin, PermisoRequeridoMixin, View):
    """Cierra una llamada pendiente al ejecutarse (RF-050)."""

    model = Llamada
    url_listado = "casos:llamadas"

    def post(self, request, pk, *args, **kwargs):
        llamada = get_object_or_404(
            acotar(request, Llamada.todos.all(), campo_delegacion_de(Llamada)), pk=pk
        )
        llamada.estado = Llamada.REALIZADA
        llamada.fecha_realizada = timezone.now()
        llamada.realizada_por = request.user
        llamada.save(update_fields=["estado", "fecha_realizada", "realizada_por"])
        registrar(request, "editar", llamada, "Cierre de llamada preventiva")
        messages.success(request, f"Llamada {llamada.referencia} cerrada.")
        return redirect(self.url_listado)
