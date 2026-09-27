from django.contrib import admin

from apps.common.admin_base import SoloLecturaAdmin
from apps.cuentas.models import PerfilUsuario, Rol


@admin.register(Rol)
class RolAdmin(SoloLecturaAdmin):
    list_display = ("nombre", "descripcion")
    search_fields = ("nombre", "descripcion")


@admin.register(PerfilUsuario)
class PerfilUsuarioAdmin(SoloLecturaAdmin):
    list_display = ("usuario", "rol", "delegacion", "estado")
    search_fields = (
        "usuario__first_name",
        "usuario__last_name",
        "usuario__email",
    )
    list_filter = ("rol", "delegacion", "estado")
    autocomplete_fields = ("rol", "delegacion")
