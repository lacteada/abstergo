"""Bitácora de auditoría.

Escribe en RegistroAuditoria desde las vistas, donde sí se conoce el usuario y
la IP de la petición.
"""

from apps.cumplimiento.models import RegistroAuditoria


def _ip(request):
    reenviada = request.META.get("HTTP_X_FORWARDED_FOR")
    if reenviada:
        return reenviada.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR") or None


def registrar(request, accion, objeto=None, detalle=""):
    usuario = getattr(request, "user", None)
    if usuario is not None and not getattr(usuario, "is_authenticated", False):
        usuario = None
    RegistroAuditoria.objects.create(
        usuario=usuario,
        accion=accion,
        tabla=objeto._meta.label if objeto is not None else "",
        objeto_id=str(getattr(objeto, "pk", "") or ""),
        ip=_ip(request),
        detalle=detalle or "",
    )
