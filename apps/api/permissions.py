"""Autorización por rol de la API.

Una sola matriz y un solo punto de aplicación: cada viewset declara qué roles
pueden leer y qué roles pueden escribir, y `PermisoPorRol` lo aplica. Ninguna
vista ramifica por rol por su cuenta.
"""

from rest_framework.permissions import SAFE_METHODS, BasePermission

# Códigos de `Rol.codigo` que existen en el sistema.
ROLES_TODOS = {
    "admin",
    "coordinador",
    "delegado",
    "funcionario",
    "verificador",
    "consulta",
}
ROLES_ESCRITURA = {"admin", "coordinador"}
ROLES_ADMIN = {"admin"}


def codigo_de(usuario):
    """El código del rol, o None si el usuario no tiene rol."""
    return usuario.rol.codigo if usuario.rol_id else None


class PermisoPorRol(BasePermission):
    """Permite según `Rol.codigo` y el método HTTP.

    El viewset declara `roles_lectura` y `roles_escritura`. El superusuario
    siempre pasa.
    """

    message = "Tu rol no tiene permiso para esta acción."

    def has_permission(self, request, view):
        usuario = request.user
        if not usuario or not usuario.is_authenticated:
            return False
        if usuario.is_superuser:
            return True
        if request.method in SAFE_METHODS:
            permitidos = getattr(view, "roles_lectura", ROLES_TODOS)
        else:
            permitidos = getattr(view, "roles_escritura", ROLES_ESCRITURA)
        return codigo_de(usuario) in permitidos
