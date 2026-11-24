"""El menú del sistema, en un solo lugar.

La misma estructura alimenta el sidebar y las acciones del panel, así el menú
no se puede desincronizar: cada ítem declara el módulo que lo habilita y quién
no lo lee no lo ve. La clave de sección marca el ítem activo.
"""

from django.urls import reverse

from apps.common.permisos import puede

# (título, ruta de la url, módulo, clave de sección)
TRABAJO = [
    ("Atenciones", "atenciones:listado", "cases", "atenciones"),
    ("Compromisos", "tubo:tablero", "tasks", "tubo"),
    ("Cartas", "tubo:cartas", "tasks", "tubo_cartas"),
    ("Actividades", "sgr:registros", "sgr_records", "sgr_registros"),
    ("Evidencias", "sgr:evidencias", "evidence", "sgr_evidencias"),
    ("Por validar", "sgr:validaciones", "validation", "sgr_validaciones"),
    ("Tablero SGR", "sgr:tablero", "sgr", "sgr_tablero"),
    ("Casos sociales", "casos:casos", "social_cases", "casos"),
    ("Organizaciones", "comunidad:organizaciones", "community", "organizaciones"),
    ("Alertas", "sgr:alertas", "alerts", "sgr_alertas"),
]

MANTENEDORES = [
    ("Delegaciones", "organizacion:delegaciones", "delegations", "delegaciones"),
    ("Territorios", "organizacion:territorios", "territories", "territorios"),
    ("Cargos", "organizacion:cargos", "positions", "cargos"),
    ("Vecinos", "ciudadanos:vecinos", "neighbors", "vecinos"),
    ("Usuarios", "cuentas:usuarios", "users", "usuarios"),
    ("Roles", "cuentas:roles", "roles", "roles"),
    ("Períodos", "sgr:periodos", "sgr", "sgr_periodos"),
    ("Áreas", "sgr:areas", "sgr", "sgr_areas"),
    ("Indicadores", "sgr:indicadores", "sgr", "sgr_indicadores"),
    ("Metas SGR", "sgr:metas", "sgr", "sgr_metas"),
    ("Metas de delegación", "catalogos:metas", "goals", "metas"),
]

GRUPOS = [
    ("trabajo", "Trabajo", TRABAJO),
    ("mantenedores", "Mantenedores", MANTENEDORES),
]


def _items(usuario, definicion):
    """Los ítems que el usuario puede leer, ya resueltos a su URL."""
    return [
        {"titulo": titulo, "url": reverse(ruta), "seccion": seccion}
        for titulo, ruta, modulo, seccion in definicion
        if puede(usuario, modulo)
    ]


def menu_de(usuario):
    """Los grupos del menú con los ítems que el usuario puede leer."""
    grupos = []
    for clave, titulo, definicion in GRUPOS:
        items = _items(usuario, definicion)
        if items:
            grupos.append({"clave": clave, "titulo": titulo, "items": items})
    return grupos
