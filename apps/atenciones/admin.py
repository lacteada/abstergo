from django.contrib import admin

from apps.atenciones.models import Atencion
from apps.common.admin_base import AdminBase


@admin.register(Atencion)
class AtencionAdmin(AdminBase):
    list_display = (
        "fecha",
        "vecino",
        "tipo_atencion",
        "delegacion",
        "funcionario",
        "estado",
    )
    search_fields = ("vecino__nombre", "vecino__rut", "motivo", "tipo_atencion__nombre")
    list_filter = ("estado", "tipo_atencion", "delegacion", "canal")
    autocomplete_fields = (
        "vecino",
        "tipo_atencion",
        "sub_atencion",
        "delegacion",
        "funcionario",
    )
    date_hierarchy = "fecha"
