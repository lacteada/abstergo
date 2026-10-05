from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.forms import BaseUserCreationForm, UserChangeForm

from apps.common.admin_base import AdminBase
from apps.cuentas.models import Rol, Usuario


class CorreoNulo:
    """Guarda el correo vacío como NULL, no como cadena vacía.

    El campo es único: dos cadenas vacías chocan contra el índice, dos NULL no.
    """

    def clean_email(self):
        return self.cleaned_data.get("email") or None


class UsuarioCrearForm(CorreoNulo, BaseUserCreationForm):
    """Alta de usuario con los dos campos de contraseña de Django.

    `BaseUserCreationForm` es la base que Django documenta para modelos de
    usuario propios: trae `password1`, `password2` y su validación.
    """

    class Meta(BaseUserCreationForm.Meta):
        model = Usuario
        fields = ("email", "first_name", "last_name", "rol", "delegacion")


class UsuarioEditarForm(CorreoNulo, UserChangeForm):
    """Edición de usuario: la contraseña se ve cifrada y no se edita aquí."""

    class Meta(UserChangeForm.Meta):
        model = Usuario
        fields = (
            "email",
            "first_name",
            "last_name",
            "rol",
            "delegacion",
            "is_active",
            "is_staff",
            "is_superuser",
            "groups",
            "user_permissions",
        )


@admin.register(Rol)
class RolAdmin(AdminBase):
    list_display = ("codigo", "nombre", "descripcion")
    search_fields = ("codigo", "nombre", "descripcion")


@admin.register(Usuario)
class UsuarioAdmin(AdminBase, BaseUserAdmin):
    form = UsuarioEditarForm
    add_form = UsuarioCrearForm
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
    ordering = ("first_name", "last_name")
    fieldsets = (
        (None, {"fields": ("email", "password")}),
        ("Datos personales", {"fields": ("first_name", "last_name")}),
        ("Asignación", {"fields": ("rol", "delegacion")}),
        (
            "Permisos",
            {
                "fields": (
                    "is_active",
                    "is_staff",
                    "is_superuser",
                    "groups",
                    "user_permissions",
                )
            },
        ),
        ("Fechas", {"fields": ("last_login", "date_joined")}),
    )
    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": (
                    "email",
                    "first_name",
                    "last_name",
                    "rol",
                    "delegacion",
                    "password1",
                    "password2",
                    "is_active",
                    "is_staff",
                ),
            },
        ),
    )

    def get_queryset(self, request):
        # El gestor de Usuario no filtra por borrado lógico; el Admin sí.
        return super().get_queryset(request).filter(eliminado__isnull=True)
