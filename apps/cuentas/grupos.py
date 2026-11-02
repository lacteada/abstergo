"""Espejo de los roles como grupos de Django.

La autorización real vive en `apps/common/permisos.py` (la matriz por rol y por
cargo). Este módulo refleja cada `Rol` como un `auth.Group` con los permisos de
Django que le corresponden, para cumplir y poder demostrar el "sistema de
permisos y grupos" y dejar `usuario.groups` poblado. El grupo no decide el
acceso: lo decide la matriz; el grupo la acompaña.
"""

from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType

from apps.atenciones.models import Atencion
from apps.catalogos.models import Meta, SubAtencion, TipoAtencion
from apps.ciudadanos.models import Vecino
from apps.common.permisos import MATRIZ
from apps.cuentas.models import Rol, Usuario
from apps.organizacion.models import Cargo, Delegacion

# Módulo de la matriz -> modelo de Django. Es el reverso de `MODELO_A_MODULO`.
MODELOS = {
    "cases": Atencion,
    "neighbors": Vecino,
    "delegations": Delegacion,
    "positions": Cargo,
    "goals": Meta,
    "attention_types": TipoAtencion,
    "attention_subtypes": SubAtencion,
    "users": Usuario,
    "roles": Rol,
}

LECTURA = ("view",)
ESCRITURA = ("add", "change", "delete")


def _permisos(rol):
    """Los permisos de Django que concede el rol, según la matriz."""
    permisos = Permission.objects.none()
    for modulo, modelo in MODELOS.items():
        reglas = MATRIZ.get(modulo)
        if not reglas:
            continue
        acciones = set()
        if rol.codigo in reglas["read"]:
            acciones |= set(LECTURA)
        if rol.codigo in reglas["write"]:
            acciones |= set(ESCRITURA)
        if not acciones:
            continue
        content_type = ContentType.objects.get_for_model(modelo)
        codenames = [f"{accion}_{modelo._meta.model_name}" for accion in acciones]
        permisos |= Permission.objects.filter(
            content_type=content_type, codename__in=codenames
        )
    return permisos


def grupo_de_rol(rol):
    """El grupo espejo del rol, creado si aún no existe."""
    if not rol:
        return None
    grupo, _ = Group.objects.get_or_create(name=rol.nombre)
    return grupo


def sincronizar_rol(rol):
    """Crea o actualiza el grupo espejo del rol."""
    if not rol or not rol.codigo:
        return None
    grupo = grupo_de_rol(rol)
    grupo.permissions.set(_permisos(rol))
    return grupo


def sincronizar_usuario(usuario):
    """Deja al usuario en el grupo de su rol, y solo en ese."""
    if not usuario.rol_id:
        if usuario.groups.exists():
            usuario.groups.clear()
        return
    grupo = grupo_de_rol(usuario.rol)
    if not grupo:
        return
    if usuario.groups.count() != 1 or not usuario.groups.filter(pk=grupo.pk).exists():
        usuario.groups.set([grupo])


def sincronizar():
    """Sincroniza los grupos de todos los roles vigentes."""
    for rol in Rol.objects.all():
        sincronizar_rol(rol)
