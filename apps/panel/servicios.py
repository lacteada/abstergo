"""El panel: qué le toca a cada rol y cómo se titula su jornada.

Cada rol ve **pocas acciones principales** (una destacada) y dos o tres números
que le importan. Los mantenedores solo aparecen para el admin.
"""

from datetime import timedelta

from django.urls import reverse
from django.utils import timezone

from apps.atenciones.models import Atencion
from apps.common.delegaciones import acotar, activa
from apps.common.permisos import (
    ADMIN,
    CONSULTA,
    COORDINADOR,
    DELEGADO,
    FUNCIONARIO,
    VERIFICADOR,
    codigo_de,
)
from apps.comunidad.models import Organizacion
from apps.sgr.models import Evidencia, RegistroGestion, Validacion
from apps.tubo.models import TareaTubo

TITULOS = {
    ADMIN: "Administración",
    COORDINADOR: "Supervisión",
    DELEGADO: "Mi delegación",
    FUNCIONARIO: "Mi jornada",
    VERIFICADOR: "Verificación",
    CONSULTA: "Consulta",
}

# (destacada, título, ruta de la url)
ACCIONES = {
    FUNCIONARIO: [
        (True, "Registrar actividad", "sgr:registros_nueva"),
        (False, "Mis actividades", "sgr:registros"),
        (False, "Mis compromisos", "tubo:tablero"),
        (False, "Mis evidencias", "sgr:evidencias"),
    ],
    DELEGADO: [
        (True, "Compromisos", "tubo:tablero"),
        (False, "Registrar atención", "atenciones:crear"),
        (False, "Mi agenda", "tubo:agenda"),
        (False, "Actividades", "sgr:registros"),
        (False, "Casos sociales", "casos:casos"),
        (False, "Tablero de delegación", "sgr:tablero"),
    ],
    VERIFICADOR: [
        (True, "Por validar", "sgr:validaciones"),
        (False, "Evidencias", "sgr:evidencias"),
    ],
    COORDINADOR: [
        (True, "Tablero global", "sgr:global"),
        (False, "Por validar", "sgr:validaciones"),
        (False, "Compromisos", "tubo:tablero"),
        (False, "Metas", "sgr:metas"),
    ],
    ADMIN: [
        (True, "Tablero SGR", "sgr:tablero"),
        (False, "Usuarios", "cuentas:usuarios"),
        (False, "Delegaciones", "organizacion:delegaciones"),
        (False, "Períodos", "sgr:periodos"),
        (False, "Organizaciones", "comunidad:organizaciones"),
    ],
    CONSULTA: [
        (True, "Tablero SGR", "sgr:tablero"),
        (False, "Actividades", "sgr:registros"),
        (False, "Organizaciones", "comunidad:organizaciones"),
    ],
}

MANTENEDORES = [
    ("Delegaciones", "organizacion:delegaciones"),
    ("Territorios", "organizacion:territorios"),
    ("Cargos", "organizacion:cargos"),
    ("Vecinos", "ciudadanos:vecinos"),
    ("Usuarios", "cuentas:usuarios"),
    ("Roles", "cuentas:roles"),
    ("Períodos", "sgr:periodos"),
    ("Áreas", "sgr:areas"),
    ("Indicadores", "sgr:indicadores"),
    ("Metas SGR", "sgr:metas"),
]


def titulo_panel(usuario):
    return TITULOS.get(codigo_de(usuario), "Panel")


def acciones_del_rol(usuario):
    """Las acciones del rol: una destacada primero y unas pocas secundarias."""
    filas = ACCIONES.get(codigo_de(usuario), ACCIONES[CONSULTA])
    return [
        {"titulo": titulo, "url": reverse(ruta), "destacada": destacada}
        for destacada, titulo, ruta in filas
    ]


def mantenedores_del_rol(usuario):
    if codigo_de(usuario) != ADMIN:
        return []
    return [{"titulo": titulo, "url": reverse(ruta)} for titulo, ruta in MANTENEDORES]


def _rango_dia(dia):
    """Rango [inicio, siguiente) del día, en hora local consciente.

    Se evita el lookup `__date`: en MySQL depende de las tablas de zona horaria
    y devuelve vacío si no están cargadas.
    """
    inicio = timezone.make_aware(
        timezone.datetime.combine(dia, timezone.datetime.min.time())
    )
    return inicio, inicio + timedelta(days=1)


def tarjetas(request):
    """Dos o tres números que importan según el rol, acotados a su ámbito."""
    usuario = request.user
    codigo = codigo_de(usuario)
    hoy = timezone.localdate()
    inicio_dia, fin_dia = _rango_dia(hoy)
    atenciones = acotar(request, Atencion.objects.all(), "delegacion")
    tareas = acotar(request, TareaTubo.objects.all(), "delegacion")
    registros = acotar(request, RegistroGestion.objects.all(), "area__delegacion")
    pendientes = acotar(
        request,
        Evidencia.objects.filter(estado_revision="pendiente"),
        "registro__area__delegacion",
    ).count()

    if codigo == FUNCIONARIO:
        return [
            (
                "Mis actividades",
                RegistroGestion.objects.filter(funcionario=usuario).count(),
            ),
            (
                "Mis compromisos abiertos",
                TareaTubo.objects.filter(responsable=usuario)
                .exclude(estado="realizada")
                .count(),
            ),
        ]
    if codigo == VERIFICADOR:
        return [
            ("Evidencias por validar", pendientes),
            (
                "Aprobadas hoy",
                Validacion.objects.filter(
                    decision="aprobada", fecha__gte=inicio_dia, fecha__lt=fin_dia
                ).count(),
            ),
        ]
    if codigo == DELEGADO:
        return [
            (
                "Atenciones de hoy",
                atenciones.filter(
                    fecha__gte=inicio_dia, fecha__lt=fin_dia
                ).count(),
            ),
            (
                "Compromisos abiertos",
                tareas.exclude(estado="realizada").count(),
            ),
            ("Evidencias por validar", pendientes),
        ]
    if codigo in (ADMIN, COORDINADOR):
        return [
            ("Actividades de hoy", registros.filter(fecha=hoy).count()),
            (
                "Compromisos abiertos",
                tareas.exclude(estado="realizada").count(),
            ),
            ("Evidencias por validar", pendientes),
            ("Organizaciones", Organizacion.objects.count()),
        ]
    return [
        ("Actividades", registros.count()),
        ("Compromisos", tareas.count()),
    ]


def resumen_visual(request):
    """Bloque compacto para el panel: estado SGR y últimas atenciones.

    Sin gráficos: un semáforo por área (del período activo) y las últimas
    atenciones del ámbito del usuario. Devuelve `None` donde no aplica.
    """
    from apps.sgr import servicios as sgr_servicios

    codigo = codigo_de(request.user)
    if codigo not in (ADMIN, COORDINADOR, DELEGADO, CONSULTA):
        return {"sgr": None, "ultimas": []}
    periodo = sgr_servicios.periodo_activo()
    resumen = (
        sgr_servicios.resumen_periodo(periodo, delegacion=activa(request))
        if periodo
        else None
    )
    ultimas = acotar(request, Atencion.objects.select_related("vecino"), "delegacion")[:6]
    return {"sgr": resumen, "ultimas": ultimas}
