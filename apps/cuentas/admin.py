from django.contrib import admin

from apps.common.admin_base import SoloLecturaAdmin
from apps.cuentas.models import Rol, Usuario


@admin.register(Rol)
class RolAdmin(SoloLecturaAdmin):
    list_display = ("nombre", "descripcion")
    search_fields = ("nombre", "descripcion")


@admin.register(Usuario)
class UsuarioAdmin(SoloLecturaAdmin):
    list_display = (
        "email",
        "first_name",
        "last_name",
        "rol",
        "delegacion",
        "is_active",
    )
    search_fields = ("email", "first_name", "last_name")
    list_filter = ("rol", "delegacion", "is_active")
    autocomplete_fields = ("rol", "delegacion")
