from django.contrib import admin

from apps.common.admin_base import AdminBase
from apps.organizacion.models import Delegacion


@admin.register(Delegacion)
class DelegacionAdmin(AdminBase):
    list_display = ("codigo", "nombre", "comuna")
    search_fields = ("codigo", "nombre", "comuna")
    list_filter = ("comuna",)
