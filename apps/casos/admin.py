from django.contrib import admin

from apps.casos.models import CasoSocial, Llamada
from apps.common.admin_base import AdminBase


@admin.register(CasoSocial)
class CasoSocialAdmin(AdminBase):
    list_display = ("referencia", "vecino", "motivo", "estado", "fecha_apertura", "responsable")
    search_fields = ("referencia", "motivo", "vecino__nombre")
    list_filter = ("estado", "reingreso")
    autocomplete_fields = ("vecino", "responsable", "caso_anterior")


@admin.register(Llamada)
class LlamadaAdmin(AdminBase):
    list_display = ("referencia", "vecino", "motivo", "fecha_programada", "estado")
    search_fields = ("referencia", "motivo", "vecino__nombre", "vecino__rut")
    list_filter = ("estado",)
    autocomplete_fields = ("vecino", "atencion", "realizada_por")
