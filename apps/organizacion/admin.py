from django.contrib import admin

from apps.common.admin_base import AdminBase
from apps.organizacion.models import Delegacion


@admin.register(Delegacion)
class DelegacionAdmin(AdminBase):
    list_display = ("codigo", "nombre", "comuna", "responsable")
    search_fields = ("codigo", "nombre", "comuna", "responsable__first_name")
    list_filter = ("comuna",)
    autocomplete_fields = ("responsable",)
