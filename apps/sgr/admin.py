from django.contrib import admin

from apps.common.admin_base import AdminBase
from apps.sgr.models import (
    AjusteConducta,
    Alerta,
    Area,
    Ausencia,
    Comentario,
    Evidencia,
    Indicador,
    MetaIndicador,
    Periodo,
    RegistroGestion,
    Validacion,
)


@admin.register(Periodo)
class PeriodoAdmin(AdminBase):
    list_display = ("codigo", "nombre", "inicio", "termino", "dias", "situacion", "estado")
    search_fields = ("codigo", "nombre")
    list_filter = ("estado", "situacion")


@admin.register(Area)
class AreaAdmin(AdminBase):
    list_display = ("codigo", "nombre", "grupo", "cargo", "responsable", "delegacion")
    search_fields = ("codigo", "nombre", "responsable__first_name")
    list_filter = ("grupo", "delegacion", "estado")
    autocomplete_fields = ("cargo", "responsable", "delegacion")


@admin.register(Indicador)
class IndicadorAdmin(AdminBase):
    list_display = ("codigo", "nombre", "grupo", "unidad", "cargo", "tipo_calculo", "estado")
    search_fields = ("codigo", "nombre")
    list_filter = ("grupo", "unidad", "tipo_calculo", "estado")
    autocomplete_fields = ("cargo",)


@admin.register(MetaIndicador)
class MetaIndicadorAdmin(AdminBase):
    list_display = ("periodo", "area", "indicador", "ponderador", "meta", "funcionario")
    search_fields = ("area__nombre", "indicador__nombre", "periodo__nombre")
    list_filter = ("periodo", "area")
    autocomplete_fields = ("periodo", "area", "indicador", "funcionario")


@admin.register(RegistroGestion)
class RegistroGestionAdmin(AdminBase):
    list_display = (
        "referencia",
        "fecha",
        "area",
        "indicador",
        "actividad",
        "funcionario",
        "etapa",
        "puntua",
        "estado",
    )
    search_fields = ("referencia", "area__nombre", "indicador__nombre", "detalle")
    list_filter = ("area", "indicador", "actividad", "etapa", "puntua", "estado", "fecha")
    autocomplete_fields = ("area", "indicador", "vecino", "funcionario", "organizacion")


@admin.register(AjusteConducta)
class AjusteConductaAdmin(AdminBase):
    list_display = ("referencia", "area", "tipo", "medio", "fecha", "valor")
    search_fields = ("referencia", "respaldo", "area__nombre")
    list_filter = ("tipo", "medio", "periodo")
    autocomplete_fields = ("area", "periodo")


@admin.register(Ausencia)
class AusenciaAdmin(AdminBase):
    list_display = ("referencia", "area", "periodo", "tipo", "desde", "hasta")
    search_fields = ("area__nombre",)
    list_filter = ("tipo", "periodo")
    autocomplete_fields = ("area", "periodo", "registrada_por")


@admin.register(Evidencia)
class EvidenciaAdmin(AdminBase):
    list_display = ("referencia", "registro", "autor", "estado_revision", "fecha")
    search_fields = ("referencia", "registro__referencia", "tipo")
    list_filter = ("estado_revision",)
    autocomplete_fields = ("registro", "autor")


@admin.register(Validacion)
class ValidacionAdmin(AdminBase):
    list_display = ("referencia", "evidencia", "verificador", "decision", "fecha")
    search_fields = ("referencia", "evidencia__referencia")
    list_filter = ("decision",)
    autocomplete_fields = ("evidencia", "verificador")


@admin.register(Comentario)
class ComentarioAdmin(AdminBase):
    list_display = ("referencia", "registro", "autor", "fecha")
    search_fields = ("referencia", "texto", "registro__referencia")
    autocomplete_fields = ("registro", "autor")


@admin.register(Alerta)
class AlertaAdmin(AdminBase):
    list_display = ("referencia", "tipo", "severidad", "mensaje", "resuelta", "area")
    search_fields = ("referencia", "mensaje", "area__nombre")
    list_filter = ("tipo", "severidad", "resuelta")
    autocomplete_fields = ("area",)
