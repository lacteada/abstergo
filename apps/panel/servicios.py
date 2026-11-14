"""Las acciones y las estadísticas del panel, fuera de la vista."""

from django.urls import reverse
from django.utils import timezone

from apps.ciudadanos.models import Vecino
from apps.common.permisos import (
    ADMIN,
    COORDINADOR,
    DELEGADO,
    FUNCIONARIO,
    alcance_global,
    codigo_de,
    modulos_de,
)
from apps.comunidad.models import Organizacion
from apps.sgr.models import Alerta, RegistroGestion
from apps.tubo.models import TareaTubo

# Título del panel por rol: le da identidad a cada dashboard.
TITULOS_PANEL = {
    ADMIN: "Panel de administración",
    COORDINADOR: "Panel de supervisión",
    DELEGADO: "Panel de delegación",
    FUNCIONARIO: "Mi jornada",
}


def titulo_panel(usuario):
    """El título del dashboard según el rol."""
    return TITULOS_PANEL.get(codigo_de(usuario), "Panel")


# Lo importante del día a día (título, ruta, descripción, módulo, escritura).
ACCIONES_TRABAJO = [
    (
        "Registrar actividad",
        "sgr:registros_nueva",
        "Anotar lo que hiciste hoy.",
        "sgr_records",
        True,
    ),
    ("Mis actividades", "sgr:registros", "Lo que has registrado.", "sgr_records", False),
    ("Tubo de trabajo", "tubo:tablero", "Las tareas de la delegación.", "tasks", False),
    (
        "Mis evidencias",
        "sgr:evidencias",
        "Archivos que respaldan lo hecho.",
        "evidence",
        False,
    ),
    (
        "Evidencias por validar",
        "sgr:validaciones",
        "Revisar lo que falta aprobar.",
        "validation",
        False,
    ),
    ("Tablero SGR", "sgr:tablero", "Cómo va el cumplimiento.", "sgr", False),
    ("Casos sociales", "casos:casos", "Acompañamiento a vecinos.", "social_cases", False),
    ("Llamadas preventivas", "casos:llamadas", "La cola de llamadas.", "social_cases", False),
    ("Cartas", "tubo:cartas", "El tubo de cartas.", "letters", False),
    (
        "Organizaciones comunitarias",
        "comunidad:organizaciones",
        "Juntas de vecinos y agrupaciones.",
        "community",
        False,
    ),
    ("Alertas", "sgr:alertas", "Avisos que requieren atención.", "alerts", False),
]

# Los CRUD y catálogos: administrativos, van aparte.
ACCIONES_MANTENEDORES = [
    (
        "Delegaciones",
        "organizacion:delegaciones",
        "Delegaciones municipales.",
        "delegations",
        False,
    ),
    ("Territorios", "organizacion:territorios", "Sectores por delegación.", "territories", False),
    ("Cargos", "organizacion:cargos", "Cargos de la delegación.", "positions", False),
    ("Vecinos", "ciudadanos:vecinos", "Mantenedor de vecinos.", "neighbors", False),
    ("Usuarios", "cuentas:usuarios", "Mantenedor de usuarios.", "users", False),
    ("Roles", "cuentas:roles", "Mantenedor de roles.", "roles", False),
    ("Períodos", "sgr:periodos", "Períodos de la matriz.", "sgr", False),
    ("Áreas", "sgr:areas", "Áreas (puestos) de la matriz.", "sgr", False),
    ("Indicadores", "sgr:indicadores", "Indicadores de la matriz.", "sgr", False),
    ("Metas SGR", "sgr:metas", "Metas por área e indicador.", "sgr", False),
    ("Metas de delegación", "catalogos:metas", "Metas por delegación.", "goals", False),
]


def _visibles(usuario, catalogo):
    """Las acciones del catálogo que el usuario puede ver, según la matriz."""
    lectura = modulos_de(usuario)
    escritura = modulos_de(usuario, escritura=True)
    return [
        {"titulo": titulo, "url": reverse(nombre), "descripcion": descripcion}
        for titulo, nombre, descripcion, modulo, requiere_escritura in catalogo
        if modulo in (escritura if requiere_escritura else lectura)
    ]


def acciones_del_rol(usuario):
    """Las acciones del día a día que el rol puede hacer."""
    return _visibles(usuario, ACCIONES_TRABAJO)


def mantenedores_del_rol(usuario):
    """Los CRUD y catálogos que el rol puede ver."""
    return _visibles(usuario, ACCIONES_MANTENEDORES)


def estadisticas(usuario):
    """Los conteos del panel, ya acotados al alcance del rol."""
    codigo = codigo_de(usuario)
    delegacion = None if alcance_global(usuario) else usuario.delegacion_id

    actividades = RegistroGestion.objects.all()
    organizaciones = Organizacion.objects.all()
    tareas = TareaTubo.objects.exclude(estado="realizada")
    if delegacion:
        actividades = actividades.filter(area__delegacion_id=delegacion)
        organizaciones = organizaciones.filter(territorio_id=delegacion)
        tareas = tareas.filter(delegacion_id=delegacion)

    datos = {
        "total_actividades": actividades.count(),
        "actividades_hoy": actividades.filter(fecha=timezone.localdate()).count(),
        "total_organizaciones": organizaciones.count(),
        "tareas_abiertas": tareas.count(),
        "alertas_pendientes": Alerta.objects.filter(resuelta=False).count(),
        "total_vecinos": Vecino.objects.count(),
    }
    if codigo == FUNCIONARIO:
        datos["mis_actividades"] = RegistroGestion.objects.filter(funcionario=usuario).count()
    return datos
