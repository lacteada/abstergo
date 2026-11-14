from django.contrib import admin

from apps.casos.models import CasoSocial, GestionCaso, Llamada
from apps.common.admin_base import AdminBase


class GestionCasoInline(admin.TabularInline):
    model = GestionCaso
    extra = 0


@admin.register(CasoSocial)
class CasoSocialAdmin(AdminBase):
    list_display = ("referencia", "vecino", "motivo", "estado", "fecha_apertura", "responsable")
    search_fields = ("referencia", "motivo", "vecino__nombre")
    list_filter = ("estado", "reingreso")
    autocomplete_fields = ("vecino", "responsable", "caso_anterior")
    inlines = (GestionCasoInline,)


@admin.register(GestionCaso)
class GestionCasoAdmin(AdminBase):
    list_display = ("referencia", "caso", "fecha", "tipo", "hito")
    search_fields = ("referencia", "detalle", "caso__referencia")
    list_filter = ("tipo", "hito")
    autocomplete_fields = ("caso",)


@admin.register(Llamada)
class LlamadaAdmin(AdminBase):
    list_display = ("referencia", "vecino", "motivo", "fecha_programada", "estado")
    search_fields = ("referencia", "motivo", "vecino__nombre")
    list_filter = ("estado",)
    autocomplete_fields = ("vecino", "responsable")
