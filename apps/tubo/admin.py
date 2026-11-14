from django.contrib import admin

from apps.common.admin_base import AdminBase
from apps.tubo.models import Carta, HistorialEstado, TareaTubo


class HistorialEstadoInline(admin.TabularInline):
    model = HistorialEstado
    extra = 0
    can_delete = False


@admin.register(TareaTubo)
class TareaTuboAdmin(AdminBase):
    list_display = (
        "referencia",
        "titulo",
        "estado",
        "delegacion",
        "responsable",
        "fecha_compromiso",
    )
    search_fields = ("referencia", "titulo", "descripcion", "responsable__first_name")
    list_filter = ("estado", "tipo", "delegacion")
    autocomplete_fields = ("delegacion", "territorio", "responsable", "apoyo", "vecino")
    inlines = (HistorialEstadoInline,)


@admin.register(Carta)
class CartaAdmin(AdminBase):
    list_display = ("referencia", "asunto", "destinatario", "estado", "fecha", "delegacion")
    search_fields = ("referencia", "asunto", "destinatario")
    list_filter = ("estado", "delegacion")
    autocomplete_fields = ("delegacion", "responsable")
