"""Generación de alertas del sistema (RF-037).

Recorre lo que puede estar en riesgo —tareas vencidas e ítems bajo umbral— y
crea las alertas que falten. Es idempotente: la misma alerta no se repite.
"""

from apps.sgr import servicios
from apps.sgr.models import Alerta, Area, RegistroGestion

UMBRAL_TELEFONO = 5
UMBRAL_CANTIDAD = 10


def generar_alertas(periodo=None):
    """Crea las alertas pendientes y devuelve cuántas se crearon."""
    creadas = _tareas_vencidas()
    creadas += _organizaciones_sin_visita()
    if periodo is not None:
        creadas += _areas_en_riesgo(periodo)
        creadas += _ingresos_sospechosos(periodo)
    return creadas


def _organizaciones_sin_visita():
    """Avisa por las organizaciones que llevan mucho sin visita (RF-060)."""
    from apps.comunidad.models import Organizacion

    creadas = 0
    for organizacion in Organizacion.objects.all():
        if organizacion.sin_visita:
            creadas += _nueva(
                "organizacion-sin-visita", "media", f"Sin visita: {organizacion.nombre}"
            )
    return creadas


def _nueva(tipo, severidad, mensaje, area=None):
    _, creada = Alerta.todos.get_or_create(
        tipo=tipo,
        area=area,
        resuelta=False,
        defaults={"severidad": severidad, "mensaje": mensaje},
    )
    return 1 if creada else 0


def _tareas_vencidas():
    from apps.tubo.models import TareaTubo

    creadas = 0
    tareas = TareaTubo.objects.exclude(fecha_compromiso=None).exclude(estado="realizada")
    for tarea in tareas:
        if tarea.vencida:
            creadas += _nueva("tarea-vencida", "alta", f"Tarea vencida: {tarea.titulo}")
    return creadas


def _areas_en_riesgo(periodo):
    creadas = 0
    for area in Area.objects.all():
        resumen = servicios.resumen_area(periodo, area)
        if any(fila["bajo_umbral"] for fila in resumen["filas"]):
            creadas += _nueva(
                "item-bajo-umbral", "media", f"{area.nombre}: ítems bajo umbral", area
            )
        if resumen["alerta_reclamos"]:
            creadas += _nueva(
                "reclamo-repetido", "alta", f"{area.nombre}: reclamos repetidos", area
            )
    return creadas


def _ingresos_sospechosos(periodo):
    """Marca registros con teléfono muy repetido o cantidad inusualmente alta."""
    from collections import Counter

    registros = list(
        RegistroGestion.objects.filter(
            fecha__gte=periodo.inicio, fecha__lte=periodo.termino, puntua=True
        )
    )
    creadas = 0
    telefonos = Counter(r.contacto_telefono for r in registros if r.contacto_telefono)
    repetidos = [numero for numero, veces in telefonos.items() if veces >= UMBRAL_TELEFONO]
    for numero in repetidos:
        creadas += _nueva(
            "ingreso-sospechoso", "alta", f"Teléfono repetido: {numero}"
        )
    altos = [r for r in registros if r.cantidad >= UMBRAL_CANTIDAD]
    if altos:
        creadas += _nueva(
            "ingreso-sospechoso", "media", f"{len(altos)} registros con cantidad alta"
        )
    return creadas
