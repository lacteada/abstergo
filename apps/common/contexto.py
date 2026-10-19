"""Contexto compartido por las plantillas."""

from apps.common.delegaciones import activa, autorizadas
from apps.common.permisos import alcance_global, codigo_de, modulos_de


def permisos(request):
    """Expone los módulos del usuario y su contexto de delegación.

    Lo que el menú y la cabecera necesitan para mostrar solo lo autorizado y
    dejar claro en qué territorio se está trabajando.
    """
    usuario = getattr(request, "user", None)
    return {
        "codigo_rol": codigo_de(usuario),
        "modulos_lectura": modulos_de(usuario),
        "modulos_escritura": modulos_de(usuario, escritura=True),
        "delegacion_activa": activa(request),
        "delegaciones_autorizadas": autorizadas(usuario),
        "alcance_global": alcance_global(usuario),
    }
