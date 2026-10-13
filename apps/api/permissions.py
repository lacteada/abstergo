"""Autorización de la API, delegada en la matriz de `apps.common.permisos`."""

from rest_framework.permissions import SAFE_METHODS, BasePermission

from apps.common.permisos import puede


class PermisoPorRol(BasePermission):
    """Deja pasar según el módulo del viewset y el método HTTP.

    Cada viewset declara `modulo`; el superusuario siempre pasa. Leer usa la
    lista de lectura de la matriz y escribir, la de escritura.
    """

    message = "Tu rol no tiene permiso para esta acción."

    def has_permission(self, request, view):
        usuario = request.user
        if not usuario or not usuario.is_authenticated:
            return False
        modulo = getattr(view, "modulo", None)
        if not modulo:
            return False
        return puede(usuario, modulo, escritura=request.method not in SAFE_METHODS)
