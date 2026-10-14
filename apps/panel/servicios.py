"""Las acciones y las estadísticas del dashboard, fuera de la vista."""

from django.urls import reverse
from django.utils import timezone

from apps.atenciones.models import Atencion
from apps.ciudadanos.models import Vecino
from apps.common.permisos import DELEGADO, FUNCIONARIO, codigo_de, modulos_de
from apps.organizacion.models import Delegacion

# (título, nombre de ruta, descripción, módulo, requiere escritura)
CATALOGO_ACCIONES = [
    ("Crear Atención", "atenciones:crear", "Registrar una atención.", "cases", True),
    ("Atenciones", "atenciones:listado", "Atenciones registradas.", "cases", False),
    ("Vecinos", "ciudadanos:vecinos", "Mantenedor de vecinos.", "neighbors", False),
    ("Delegaciones", "organizacion:delegaciones", "Delegaciones.", "delegations", False),
    ("Usuarios", "cuentas:usuarios", "Mantenedor de usuarios.", "users", False),
    ("Roles", "cuentas:roles", "Mantenedor de roles.", "roles", False),
    ("Metas", "catalogos:metas", "Metas por delegación.", "goals", False),
    ("Tipos de atención", "catalogos:tipos", "Tipos de atención.", "attention_types", False),
    ("Sub atenciones", "catalogos:subatenciones", "Sub atenciones.", "attention_subtypes", False),
]


def acciones_del_rol(usuario):
    """Las acciones del dashboard que el rol puede hacer, según la matriz."""
    lectura = modulos_de(usuario)
    escritura = modulos_de(usuario, escritura=True)
    return [
        {"titulo": titulo, "url": reverse(nombre), "descripcion": descripcion}
        for titulo, nombre, descripcion, modulo, requiere_escritura in CATALOGO_ACCIONES
        if modulo in (escritura if requiere_escritura else lectura)
    ]


def _atenciones_visibles(usuario, codigo):
    """Un funcionario o delegado solo ve las atenciones de su delegación."""
    atenciones = Atencion.objects.all()
    if codigo in (FUNCIONARIO, DELEGADO) and usuario.delegacion_id:
        atenciones = atenciones.filter(delegacion_id=usuario.delegacion_id)
    return atenciones


def estadisticas(usuario):
    """Los conteos del dashboard, ya acotados al alcance del rol."""
    codigo = codigo_de(usuario)
    atenciones = _atenciones_visibles(usuario, codigo)
    datos = {
        "total_atenciones": atenciones.count(),
        "atenciones_hoy": atenciones.filter(fecha__date=timezone.localdate()).count(),
        "total_vecinos": Vecino.objects.count(),
        "total_delegaciones": Delegacion.objects.count(),
    }
    if codigo == FUNCIONARIO:
        datos["mis_atenciones"] = Atencion.objects.filter(funcionario=usuario).count()
    return datos
