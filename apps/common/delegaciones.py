"""El contexto de delegación, en un solo lugar.

Cada usuario tiene una delegación principal (`Usuario.delegacion`) y, si su
perfil trabaja en más de un territorio, un conjunto de autorizadas
(`Usuario.delegaciones_autorizadas`). La **delegación activa** es la que el
usuario eligió con el selector; si no eligió ninguna válida, es la principal.

Los roles de alcance global (admin y coordinador) no se acotan a un territorio:
su delegación activa es "todas" y ven el sistema completo.
"""

from apps.common.permisos import alcance_global
from apps.organizacion.models import Delegacion

CLAVE_SESION = "delegacion_activa"


def autorizadas(usuario):
    """Las delegaciones que el perfil puede usar.

    Un rol global ve todas; el resto, las que tenga en `delegaciones_autorizadas`
    más su principal, sin repetir.
    """
    if not usuario or not usuario.is_authenticated:
        return Delegacion.objects.none()
    if alcance_global(usuario):
        return Delegacion.objects.all()
    ids = set(usuario.delegaciones_autorizadas.values_list("pk", flat=True))
    if usuario.delegacion_id:
        ids.add(usuario.delegacion_id)
    return Delegacion.objects.filter(pk__in=ids)


def activa(request):
    """La delegación activa, validada contra las autorizadas del usuario.

    Devuelve `None` cuando el rol es global y no eligió ninguna: en ese caso ve
    todos los registros. Un rol acotado parte siempre de su delegación principal.
    """
    usuario = getattr(request, "user", None)
    disponibles = autorizadas(usuario)
    elegida = request.session.get(CLAVE_SESION)
    if elegida and disponibles.filter(pk=elegida).exists():
        return disponibles.get(pk=elegida)
    if alcance_global(usuario):
        return None
    principal = getattr(usuario, "delegacion", None)
    if principal and disponibles.filter(pk=principal.pk).exists():
        return principal
    return disponibles.first()


def acotar(request, queryset, campo):
    """Filtra el queryset por la delegación activa.

    `campo` es la ruta del campo que apunta a la delegación ("delegacion",
    "territorio"). Para el propio modelo Delegacion se usa el valor especial
    "pk", que compara contra la clave de la delegación activa: `pk` es un
    entero, así que hay que pasar el número y no el objeto.
    """
    delegacion = activa(request)
    if delegacion is None:
        return queryset
    if campo == "pk":
        return queryset.filter(pk=delegacion.pk)
    return queryset.filter(**{campo: delegacion})
