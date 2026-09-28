from django.contrib import admin

from apps.common.admin_base import SoloLecturaAdmin
from apps.catalogos.models import Meta, SubAtencion, TipoAtencion


@admin.register(Meta)
class MetaAdmin(SoloLecturaAdmin):
    list_display = ("nombre", "delegacion", "descripcion")
    search_fields = ("nombre", "descripcion", "delegacion__nombre")
    list_filter = ("delegacion",)
    autocomplete_fields = ("delegacion",)


@admin.register(TipoAtencion)
class TipoAtencionAdmin(SoloLecturaAdmin):
    list_display = ("nombre", "descripcion")
    search_fields = ("nombre", "descripcion")


@admin.register(SubAtencion)
class SubAtencionAdmin(SoloLecturaAdmin):
    list_display = ("nombre", "tipo_atencion")
    search_fields = ("nombre", "tipo_atencion__nombre")
    list_filter = ("tipo_atencion",)
    autocomplete_fields = ("tipo_atencion",)
