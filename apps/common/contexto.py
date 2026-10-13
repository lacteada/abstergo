"""Contexto compartido por las plantillas."""

from apps.common.permisos import codigo_de, modulos_de


def permisos(request):
    """Expone los módulos que el usuario puede leer y escribir, para el menú."""
    usuario = getattr(request, "user", None)
    return {
        "codigo_rol": codigo_de(usuario),
        "modulos_lectura": modulos_de(usuario),
        "modulos_escritura": modulos_de(usuario, escritura=True),
    }
