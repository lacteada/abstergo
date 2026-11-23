"""Armado de los tableros de la Matriz SGR (delegación, personal y global).

Junta, por período, lo avanzado en cada área (registros que puntúan) con su meta
y su ponderador, y le aplica el cálculo puro de `calculos.py`. La vista solo
renderiza lo que esta capa devuelve.
"""

from decimal import Decimal

from django.db.models import Q
from django.utils import timezone

from apps.sgr import calculos
from apps.sgr.models import (
    ESTADOS_VALIDOS,
    AjusteConducta,
    Area,
    Ausencia,
    MetaIndicador,
    Periodo,
    RegistroGestion,
)
from apps.sgr.validaciones import MAX_FELICITACIONES, VALOR_FELICITACION

MAX_RECLAMOS = 2


def periodo_activo(pk=None):
    """El período pedido, o el más reciente si no hay ninguno."""
    if pk:
        elegido = Periodo.objects.filter(pk=pk).first()
        if elegido:
            return elegido
    return Periodo.objects.order_by("-inicio").first()


def _avance(periodo, area, indicador):
    """La cantidad de gestiones que puntúan de un área/indicador en el período.

    Si el ítem exige evidencia validada, solo cuentan los registros aprobados
    (RN-010); si no, los estados válidos corrientes.
    """
    estados = ("aprobada",) if indicador.requiere_evidencia else ESTADOS_VALIDOS
    registros = RegistroGestion.objects.filter(
        area=area,
        indicador=indicador,
        fecha__gte=periodo.inicio,
        fecha__lte=periodo.termino,
        puntua=True,
        estado__in=estados,
    )
    return sum(registro.cantidad for registro in registros)


def _conductas(periodo, area):
    conductas = AjusteConducta.objects.filter(area=area)
    if periodo:
        conductas = conductas.filter(periodo=periodo)
    return list(conductas)


def _ajuste_conductas(periodo, area):
    """La suma de reclamos y felicitaciones del área (doc 3)."""
    conductas = _conductas(periodo, area)
    felicitaciones = [c for c in conductas if c.tipo == "felicitacion"]
    exceso = max(0, len(felicitaciones) - MAX_FELICITACIONES)
    valor = sum((c.valor for c in conductas), Decimal("0"))
    # Solo se permiten 3 felicitaciones: se descuentan las de más.
    if exceso:
        valor -= VALOR_FELICITACION * exceso
    return valor


def _dias_ausencia(periodo, area):
    """Días de ausencia del área en el período (RF-048, RN-008)."""
    ausencias = Ausencia.objects.filter(area=area).filter(
        Q(periodo=periodo) | Q(periodo__isnull=True)
    )
    return sum(ausencia.dias for ausencia in ausencias)


def _fraccion(periodo, area):
    """Fracción computable del período, descontando las ausencias del área."""
    total = periodo.dias_totales
    if total <= 0:
        return 0.0
    computables = max(0, periodo.dias_transcurridos() - _dias_ausencia(periodo, area))
    return min(1.0, computables / total)


def resumen_area(periodo, area):
    """El detalle de un área: indicadores, ponderado, semáforo y alertas."""
    fraccion = _fraccion(periodo, area)
    filas = []
    for meta in MetaIndicador.objects.filter(periodo=periodo, area=area):
        avance = _avance(periodo, area, meta.indicador)
        porcentaje = calculos.porcentaje(avance, meta.meta, periodo.tope_item)
        filas.append(
            {
                "indicador": meta.indicador,
                "ponderador": meta.ponderador,
                "meta": meta.meta,
                "avance": avance,
                "porcentaje": porcentaje,
                "ponderado": calculos.ponderado(
                    meta.ponderador, avance, meta.meta, periodo.tope_item
                ),
                "bajo_umbral": porcentaje < periodo.umbral_minimo,
                "en_tope": porcentaje >= periodo.tope_item,
            }
        )
    logrado = sum((fila["ponderado"] for fila in filas), Decimal("0"))
    logrado += _ajuste_conductas(periodo, area)
    suma_ponderadores = sum((fila["ponderador"] for fila in filas), Decimal("0"))
    esperado = suma_ponderadores * Decimal(str(fraccion))
    reclamos = len([c for c in _conductas(periodo, area) if c.tipo == "reclamo"])
    registros = RegistroGestion.objects.filter(
        area=area, fecha__gte=periodo.inicio, fecha__lte=periodo.termino
    )
    ultimo = registros.order_by("-fecha").values_list("fecha", flat=True).first()
    ingresos = registros.count()
    dias = periodo.dias_transcurridos() or 1
    logrado_total = calculos.total_ponderado([logrado], periodo.tope_total)
    esperado_total = calculos.meta_al_dia(esperado, 1)
    return {
        "area": area,
        "filas": filas,
        "logrado": logrado_total,
        "esperado": esperado_total,
        "relativo": calculos.relativo(logrado_total, esperado_total),
        "semaforo": calculos.semaforo(logrado, esperado, periodo.umbral_ambar),
        "reclamos": reclamos,
        "alerta_reclamos": reclamos > MAX_RECLAMOS,
        # RN-001: la suma de ponderadores del área debe dar 100 %, salvo la
        # excepción configurada. No bloquea: advierte.
        "suma_ponderadores": suma_ponderadores,
        "suma_incompleta": suma_ponderadores != Decimal("1")
        and not area.excepcion_ponderadores,
        # RF-030: actividad reciente del área.
        "ultimo_ingreso": ultimo,
        "dias_sin_ingreso": (timezone.localdate() - ultimo).days if ultimo else None,
        "ingresos": ingresos,
        "promedio_diario": round(ingresos / dias, 2),
    }


def resumen_periodo(periodo, delegacion=None):
    """Todas las áreas del período (opcionalmente de una delegación) y totales."""
    if not periodo:
        return {"periodo": None, "areas": [], "totales": {}}
    areas = Area.objects.select_related("cargo", "responsable", "delegacion")
    if delegacion is not None:
        areas = areas.filter(delegacion=delegacion)
    resumen = [resumen_area(periodo, area) for area in areas.order_by("grupo", "nombre")]
    logrado = sum((fila["logrado"] for fila in resumen), Decimal("0"))
    esperado = sum((fila["esperado"] for fila in resumen), Decimal("0"))
    promedio = logrado / len(resumen) if resumen else Decimal("0")
    promedio_esperado = esperado / len(resumen) if resumen else Decimal("0")
    return {
        "periodo": periodo,
        "fraccion": periodo.fraccion_transcurrida(),
        "areas": resumen,
        "totales": {
            "logrado": logrado,
            "esperado": esperado,
            "relativo": calculos.relativo(logrado, esperado),
            "promedio": promedio,
            "promedio_esperado": promedio_esperado,
            "semaforo": calculos.semaforo(logrado, esperado, periodo.umbral_ambar),
        },
    }


def resumen_por_cargo(periodo):
    """Consolida las áreas por cargo (vista global, RF-031)."""
    if not periodo:
        return []
    grupos = {}
    for area in Area.objects.select_related("cargo").order_by("nombre"):
        clave = area.cargo.nombre if area.cargo_id else "Sin cargo"
        item = resumen_area(periodo, area)
        fila = grupos.setdefault(
            clave,
            {"cargo": clave, "areas": 0, "logrado": Decimal("0"), "esperado": Decimal("0")},
        )
        fila["areas"] += 1
        fila["logrado"] += item["logrado"]
        fila["esperado"] += item["esperado"]
    for fila in grupos.values():
        fila["promedio"] = fila["logrado"] / fila["areas"] if fila["areas"] else Decimal("0")
        fila["promedio_esperado"] = (
            fila["esperado"] / fila["areas"] if fila["areas"] else Decimal("0")
        )
        fila["relativo"] = calculos.relativo(fila["logrado"], fila["esperado"])
        fila["semaforo"] = calculos.semaforo(
            fila["logrado"], fila["esperado"], periodo.umbral_ambar
        )
    return sorted(grupos.values(), key=lambda fila: fila["cargo"])
