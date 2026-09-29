from django.contrib import admin

from apps.common.admin_base import AdminBase
from apps.catalogos.models import Meta, SubAtencion, TipoAtencion


@admin.register(Meta)
class MetaAdmin(AdminBase):
    list_display = ("nombre", "delegacion", "descripcion")
    search_fields = ("nombre", "descripcion", "delegacion__nombre")
    list_filter = ("delegacion",)
    autocomplete_fields = ("delegacion",)


@admin.register(TipoAtencion)
class TipoAtencionAdmin(AdminBase):
    list_display = ("nombre", "descripcion")
    search_fields = ("nombre", "descripcion")


@admin.register(SubAtencion)
class SubAtencionAdmin(AdminBase):
    list_display = ("nombre", "tipo_atencion")
    search_fields = ("nombre", "tipo_atencion__nombre")
    list_filter = ("tipo_atencion",)
    autocomplete_fields = ("tipo_atencion",)
