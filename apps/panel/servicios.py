"""El panel: qué le toca a cada rol y cómo se titula su jornada.

Cada rol ve **pocas acciones principales** (una destacada) y dos o tres números
que le importan. Los mantenedores solo aparecen para el admin.
"""

from datetime import timedelta

from django.urls import reverse
from django.utils import timezone

from apps.atenciones.models import Atencion
from apps.common.delegaciones import acotar, activa
from apps.common.menu import MANTENEDORES as MENU_MANTENEDORES
from apps.common.permisos import (
    ADMIN,
    CONSULTA,
    COORDINADOR,
    DELEGADO,
    FUNCIONARIO,
    VERIFICADOR,
    codigo_de,
    puede,
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

# (destacada, título, ruta de la url, módulo que la habilita)
ACCIONES = {
    FUNCIONARIO: [
        (True, "Registrar actividad", "sgr:registros_nueva", "sgr_records"),
        (False, "Mis actividades", "sgr:registros", "sgr_records"),
        (False, "Mis compromisos", "tubo:tablero", "tasks"),
        (False, "Mis evidencias", "sgr:evidencias", "evidence"),
    ],
    DELEGADO: [
        (True, "Compromisos", "tubo:tablero", "tasks"),
        (False, "Registrar atención", "atenciones:crear", "cases"),
        (False, "Mi agenda", "tubo:agenda", "tasks"),
        (False, "Actividades", "sgr:registros", "sgr_records"),
        (False, "Casos sociales", "casos:casos", "social_cases"),
    ],
    VERIFICADOR: [
        (True, "Por validar", "sgr:validaciones", "validation"),
        (False, "Evidencias", "sgr:evidencias", "evidence"),
    ],
    COORDINADOR: [
        (True, "Tablero global", "sgr:global", "sgr"),
        (False, "Por validar", "sgr:validaciones", "validation"),
        (False, "Compromisos", "tubo:tablero", "tasks"),
        (False, "Metas", "sgr:metas", "goals"),
    ],
    ADMIN: [
        (True, "Tablero SGR", "sgr:tablero", "sgr"),
        (False, "Usuarios", "cuentas:usuarios", "users"),
        (False, "Delegaciones", "organizacion:delegaciones", "delegations"),
        (False, "Períodos", "sgr:periodos", "sgr"),
        (False, "Organizaciones", "comunidad:organizaciones", "community"),
    ],
    CONSULTA: [
        (True, "Tablero SGR", "sgr:tablero", "sgr"),
        (False, "Actividades", "sgr:registros", "sgr_records"),
        (False, "Organizaciones", "comunidad:organizaciones", "community"),
    ],
}


def titulo_panel(usuario):
    return TITULOS.get(codigo_de(usuario), "Panel")


def acciones_del_rol(usuario):
    """Las acciones del rol: una destacada primero y unas pocas secundarias.

    Solo las que el usuario puede abrir: la misma matriz decide qué se ve, así
    no quedan enlaces que terminen en 403.
    """
    filas = ACCIONES.get(codigo_de(usuario), ACCIONES[CONSULTA])
    return [
        {"titulo": titulo, "url": reverse(ruta), "destacada": destacada}
        for destacada, titulo, ruta, modulo in filas
        if puede(usuario, modulo)
    ]


def mantenedores_del_rol(usuario):
    """Los mantenedores del panel: solo para quien administra, desde el menú."""
    if codigo_de(usuario) != ADMIN:
        return []
    return [
        {"titulo": titulo, "url": reverse(ruta)}
        for titulo, ruta, modulo, _ in MENU_MANTENEDORES
        if puede(usuario, modulo)
    ]


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
    """Bloque del panel: el tablero SGR del período activo y últimas atenciones.

    El tablero completo (áreas, meta al día, avance y semáforo) se muestra en el
    dashboard para los roles que leen SGR; las últimas atenciones acompañan.
    Devuelve `None` donde no aplica.
    """
    from apps.sgr import servicios as sgr_servicios

    codigo = codigo_de(request.user)
    if codigo not in (ADMIN, COORDINADOR, DELEGADO, CONSULTA):
        return {"resumen_sgr": None, "ultimas": []}
    from apps.common import periodo as periodo_contexto

    periodo = periodo_contexto.activa(request)
    resumen = (
        sgr_servicios.resumen_periodo(periodo, delegacion=activa(request))
        if periodo
        else None
    )
    ultimas = acotar(request, Atencion.objects.select_related("vecino"), "delegacion")[:6]
    return {"resumen_sgr": resumen, "ultimas": ultimas}
