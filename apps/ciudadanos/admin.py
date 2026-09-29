from django.contrib import admin

from apps.common.admin_base import AdminBase
from apps.ciudadanos.models import Vecino


@admin.register(Vecino)
class VecinoAdmin(AdminBase):
    list_display = (
        "nombre",
        "rut",
        "direccion",
        "telefono",
        "territorio",
        "tipo_gestion",
        "estado",
    )
    search_fields = (
        "nombre",
        "rut",
        "direccion",
        "telefono",
        "territorio__nombre",
        "tipo_gestion",
    )
    list_filter = ("territorio", "estado")
    autocomplete_fields = ("territorio",)
