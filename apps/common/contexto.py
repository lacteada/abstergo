"""Contexto compartido por las plantillas."""

from apps.common import periodo
from apps.common.delegaciones import activa, autorizadas
from apps.common.permisos import alcance_global, codigo_de, modulos_de


def permisos(request):
    """Expone los módulos del usuario y su contexto de trabajo.

    Lo que el menú y la cabecera necesitan para mostrar solo lo autorizado y
    dejar claro en qué territorio y en qué período se está trabajando.
    """
    usuario = getattr(request, "user", None)
    contexto = {
        "codigo_rol": codigo_de(usuario),
        "modulos_lectura": modulos_de(usuario),
        "modulos_escritura": modulos_de(usuario, escritura=True),
        "delegacion_activa": activa(request),
        "delegaciones_autorizadas": autorizadas(usuario),
        "alcance_global": alcance_global(usuario),
    }
    if usuario is not None and usuario.is_authenticated:
        contexto["periodo_activo"] = periodo.activa(request)
        contexto["periodos"] = periodo.disponibles()
    return contexto
