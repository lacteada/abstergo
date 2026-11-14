"""Reglas de negocio del 4° trimestre (documento 1).

Funciones puras y cortas: no consultan la base. Las vistas y los modelos les
pasan los datos ya contados.
"""

from datetime import timedelta
from decimal import Decimal

# Doc 1, punto 3: el ingreso diario no puede superar las 7 gestiones.
MAX_REGISTROS_DIA = 7

# Doc 1, reglas 7 y 8: valor de cada reclamo y de cada felicitación.
VALOR_RECLAMO = Decimal("-0.2")
VALOR_FELICITACION = Decimal("0.1")
MAX_FELICITACIONES = 3

# Algunos cargos rebajan más el reclamo (doc 3: −0.3 en Apoyo Administrativo).
VALORES_RECLAMO_POR_CARGO = {"apoyo-administrativo": Decimal("-0.3")}


def lunes_de(fecha):
    """El lunes de la semana a la que pertenece `fecha`."""
    return fecha - timedelta(days=fecha.weekday())


def en_semana_actual(fecha, hoy):
    """¿La fecha cae en la semana en curso? (doc 1, punto 4).

    La semana se cierra el lunes siguiente: lo anterior al lunes de esta semana
    ya no se puede ingresar.
    """
    return fecha >= lunes_de(hoy)


def excede_tope_diario(ingresados, extra=1, tope=MAX_REGISTROS_DIA):
    """¿Estos ingresos, sumados a los ya hechos, pasan el máximo del día?"""
    return ingresados + extra > tope


def valor_conducta(tipo, cargo=None):
    """El valor por defecto de un reclamo o una felicitación (el reclamo varía por cargo)."""
    if tipo == "reclamo":
        return VALORES_RECLAMO_POR_CARGO.get(cargo, VALOR_RECLAMO)
    return VALOR_FELICITACION


def evaluar_puntaje(etapa, tipo_solicitante, contacto_nombre, contacto_telefono):
    """Decide si una gestión puntúa y, si no, por qué (C1, C2, C5).

    Devuelve `(puntua, motivo)`. Reglas del correo: la etapa preparatoria no
    puntúa, el solicitante delegado es "otra gestión", y sin nombre y teléfono
    del usuario no hay puntaje.
    """
    if etapa != "ejecutada":
        return False, "Etapa preparatoria: no puntúa."
    if tipo_solicitante == "delegado":
        return False, "El solicitante es el delegado: otra gestión."
    if not (contacto_nombre and contacto_telefono):
        return False, "Falta nombre o teléfono del usuario."
    return True, ""
