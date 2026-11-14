from django.contrib import admin

from apps.common.admin_base import AdminBase
from apps.comunidad.models import Organizacion


@admin.register(Organizacion)
class OrganizacionAdmin(AdminBase):
    list_display = ("codigo", "nombre", "territorio", "socios_activos", "estado")
    search_fields = ("codigo", "nombre", "domicilio_legal", "registro_pj")
    list_filter = ("territorio", "estado")
    autocomplete_fields = ("territorio",)
