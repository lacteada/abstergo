"""El panel: qué le toca a cada rol y cómo se titula su jornada.

Cada rol ve **pocas acciones principales** (una destacada) y dos o tres números
que le importan. Los mantenedores solo aparecen para el admin.
"""

from datetime import timedelta

from django.urls import reverse
from django.utils import timezone

from apps.atenciones.models import Atencion
from apps.casos.models import Llamada
from apps.common.delegaciones import acotar, activa
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
from apps.sgr.models import Alerta, Evidencia, RegistroGestion, Validacion
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
    filas = [(False, "Buzón de trabajo", "panel:buzon")] + ACCIONES.get(
        codigo_de(usuario), ACCIONES[CONSULTA]
    )
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


# -------------------------------------------------------------- Buzón de trabajo
# Importancia de cada ítem: 1 es lo más urgente. Dentro de una prioridad se
# ordena por la fecha relevante, con lo más atrasado primero.
PRIORIDADES = [
    (1, "Crítico"),
    (2, "Alto"),
    (3, "Medio"),
    (4, "Bajo"),
]

# Un ítem sin fecha se ordena al final de su grupo.
SIN_FECHA = timezone.datetime.max.date()


def _fecha(valor):
    """La fecha de un ítem como `date`, para poder ordenar entre módulos."""
    if valor is None:
        return SIN_FECHA
    return valor.date() if hasattr(valor, "date") else valor


def _fila(prioridad, tipo, codigo, titulo, detalle, fecha, url, color, traza="", vencido=False):
    """Un ítem del buzón, con su enlace al detalle y a la trazabilidad."""
    return {
        "prioridad": prioridad,
        "tipo": tipo,
        "codigo": codigo,
        "titulo": titulo,
        "detalle": detalle,
        "fecha": _fecha(fecha),
        "vencido": vencido,
        "color": color,
        "url": url,
        "traza": traza,
    }


def buzon(request):
    """El trabajo accionable de todos los módulos, ordenado por importancia.

    Reúne lo pendiente de acción en cada módulo que el perfil puede leer
    (compromisos abiertos, actividades por corregir, evidencias por validar,
    llamadas y alertas), con enlace al detalle y a la trazabilidad de cada uno.
    El ámbito lo fija `acotar`: global para admin y coordinador, por delegación
    para el resto.
    """
    usuario = request.user
    hoy = timezone.localdate()
    items = []

    if puede(usuario, "tasks"):
        abiertas = acotar(
            request, TareaTubo.objects.select_related("delegacion"), "delegacion"
        ).exclude(estado="realizada")
        for tarea in abiertas:
            vencida = tarea.vencida
            items.append(
                _fila(
                    prioridad=1 if vencida else 3,
                    tipo="Compromiso",
                    codigo=tarea.referencia,
                    titulo=tarea.titulo,
                    detalle=f"{tarea.delegacion.nombre} · {tarea.get_estado_display()}",
                    fecha=tarea.fecha_compromiso,
                    url=reverse("tubo:tareas_consultar", args=[tarea.pk]),
                    traza=reverse("tubo:tareas_historial", args=[tarea.pk]),
                    color="rojo" if vencida else "ambar",
                    vencido=vencida,
                )
            )

    if puede(usuario, "sgr_records"):
        por_corregir = acotar(
            request,
            RegistroGestion.objects.select_related("area", "indicador"),
            "area__delegacion",
        ).filter(estado__in=["correccion", "rechazada"])
        for registro in por_corregir:
            items.append(
                _fila(
                    prioridad=2,
                    tipo="Actividad",
                    codigo=registro.referencia,
                    titulo=f"{registro.indicador.nombre} · {registro.area.nombre}",
                    detalle=registro.get_estado_display(),
                    fecha=registro.fecha,
                    url=reverse("sgr:registros_consultar", args=[registro.pk]),
                    color="rojo",
                )
            )

    if puede(usuario, "evidence"):
        por_validar = acotar(
            request,
            Evidencia.objects.select_related("registro__indicador"),
            "registro__area__delegacion",
        ).filter(estado_revision="pendiente")
        for evidencia in por_validar:
            items.append(
                _fila(
                    prioridad=2,
                    tipo="Evidencia",
                    codigo=evidencia.referencia,
                    titulo=evidencia.registro.indicador.nombre,
                    detalle="Pendiente de validación",
                    fecha=evidencia.fecha,
                    url=reverse("sgr:evidencias_consultar", args=[evidencia.pk]),
                    traza=reverse(
                        "sgr:registros_consultar", args=[evidencia.registro_id]
                    ),
                    color="ambar",
                )
            )

    if puede(usuario, "cases"):
        llamadas = acotar(
            request, Llamada.objects.select_related("vecino"), "atencion__delegacion"
        ).filter(estado="pendiente")
        for llamada in llamadas:
            vencida = bool(llamada.fecha_programada and llamada.fecha_programada < hoy)
            items.append(
                _fila(
                    prioridad=2 if vencida else 3,
                    tipo="Llamada",
                    codigo=llamada.referencia,
                    titulo=f"Llamar a {llamada.vecino.nombre}",
                    detalle=llamada.motivo or "Seguimiento preventivo",
                    fecha=llamada.fecha_programada,
                    url=reverse("casos:llamadas_consultar", args=[llamada.pk]),
                    color="rojo" if vencida else "ambar",
                    vencido=vencida,
                )
            )

    if puede(usuario, "alerts"):
        pendientes = acotar(
            request, Alerta.objects.select_related("area"), "area__delegacion"
        ).filter(resuelta=False)
        for alerta in pendientes:
            items.append(
                _fila(
                    prioridad={"alta": 1, "media": 2, "baja": 4}.get(
                        alerta.severidad, 3
                    ),
                    tipo="Alerta",
                    codigo=alerta.referencia,
                    titulo=alerta.mensaje,
                    detalle=(
                        f"{alerta.get_tipo_display()} · "
                        f"severidad {alerta.get_severidad_display()}"
                    ),
                    fecha=alerta.fecha,
                    url=reverse("sgr:alertas_consultar", args=[alerta.pk]),
                    color="rojo" if alerta.severidad == "alta" else "gris",
                )
            )

    items.sort(key=lambda item: (item["prioridad"], item["fecha"]))

    grupos = [
        {
            "prioridad": prioridad,
            "titulo": titulo,
            "items": [item for item in items if item["prioridad"] == prioridad],
        }
        for prioridad, titulo in PRIORIDADES
    ]
    return {
        "total": len(items),
        "grupos": [grupo for grupo in grupos if grupo["items"]],
        "resumen": [
            {"titulo": "EN EL BUZÓN", "numero": len(items), "color": "rojo"},
            {
                "titulo": "CRÍTICOS",
                "numero": len([i for i in items if i["prioridad"] == 1]),
                "color": "rojo",
            },
            {
                "titulo": "VENCIDOS",
                "numero": len([i for i in items if i["vencido"]]),
                "color": "ambar",
            },
            {
                "titulo": "POR VALIDAR",
                "numero": len([i for i in items if i["tipo"] == "Evidencia"]),
                "color": "verde",
            },
        ],
    }
