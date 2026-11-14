from django.contrib import admin

from apps.casos.models import CasoSocial
from apps.common.admin_base import AdminBase


@admin.register(CasoSocial)
class CasoSocialAdmin(AdminBase):
    list_display = ("referencia", "vecino", "motivo", "estado", "fecha_apertura", "responsable")
    search_fields = ("referencia", "motivo", "vecino__nombre")
    list_filter = ("estado", "reingreso")
    autocomplete_fields = ("vecino", "responsable", "caso_anterior")
