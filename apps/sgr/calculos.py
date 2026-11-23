"""Cálculo del puntaje de la Matriz SGR — dominio puro, sin framework.

Define las constantes y la aritmética del semáforo, el porcentaje de
cumplimiento y el puntaje ponderado. No toca la base de datos: recibe números
y devuelve números, por eso se puede probar sin Django.
"""

from decimal import Decimal

# Tope por ítem (doc 1: un ítem no sube más allá del 120 %) y al total del
# cumplimiento (doc 3: máximo 150 %). Se aplican por separado.
TOPE_ITEM = Decimal("1.2")
TOPE_TOTAL = Decimal("1.5")

# Una persona bajo el 60 % de su meta al día queda en rojo (deducido de la
# muestra del documento 3).
FACTOR_SEMAFORO = Decimal("0.6")

VERDE = "verde"
NARANJA = "naranja"
ROJO = "rojo"

TRES_DECIMALES = Decimal("0.001")


def porcentaje(avance, meta, tope=TOPE_ITEM):
    """Cumplimiento de un ítem, recortado en el tope (1.2 por defecto)."""
    if not meta or Decimal(meta) <= 0:
        return Decimal("0")
    valor = Decimal(avance) / Decimal(meta)
    return min(valor, tope)


def ponderado(ponderador, avance, meta, tope=TOPE_ITEM):
    """Cumplimiento ponderado: ponderador × porcentaje."""
    return (Decimal(ponderador) * porcentaje(avance, meta, tope)).quantize(
        TRES_DECIMALES
    )


def relativo(logrado, objetivo):
    """Cuánto se ha cumplido respecto de la meta al día, sin tope.

    Es el número que lee la persona: 1 (100 %) significa que va al día,
    más de 1 adelantada y menos de 1 atrasada.
    """
    if not objetivo or Decimal(objetivo) <= 0:
        return Decimal("0")
    return (Decimal(logrado) / Decimal(objetivo)).quantize(TRES_DECIMALES)


def semaforo(avance, objetivo, factor=FACTOR_SEMAFORO):
    """Color del cumplimiento contra la meta al día.

    VERDE: llegó o superó la meta. NARANJA: al menos `factor` (60 % por
    defecto, configurable por período). ROJO: debajo.
    """
    avance = Decimal(avance)
    objetivo = Decimal(objetivo)
    if objetivo <= 0 or avance >= objetivo:
        return VERDE
    if avance >= factor * objetivo:
        return NARANJA
    return ROJO


def meta_al_dia(meta, fraccion):
    """La parte de la meta que debería estar cumplida a la fecha."""
    return (Decimal(meta) * Decimal(str(fraccion))).quantize(TRES_DECIMALES)


def total_ponderado(items, tope=TOPE_TOTAL):
    """La suma de los cumplimientos ponderados, con el tope total."""
    suma = sum((Decimal(valor) for valor in items), Decimal("0"))
    return min(suma, tope).quantize(TRES_DECIMALES)
