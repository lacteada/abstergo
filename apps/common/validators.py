"""Validadores por expresión regular compartidos por los mantenedores.

Los patrones aceptan los datos que ya vienen en datos_nuevos/, así que los
registros existentes siguen siendo editables.
"""

import re

from django.core.exceptions import ValidationError

PATRON_NOMBRE = re.compile(r"^[A-Za-zÁÉÍÓÚÑáéíóúñÜü' -]{2,60}$")
PATRON_TELEFONO = re.compile(r"^\d{8,13}$")
PATRON_DIRECCION = re.compile(r"^[A-Za-z0-9ÁÉÍÓÚÑáéíóúñ°#.,\- ]{5,200}$")
PATRON_COMUNA = re.compile(r"^[A-Za-zÁÉÍÓÚÑáéíóúñ' ]{3,80}$")
PATRON_CODIGO = re.compile(r"^[A-Za-z0-9-]{2,40}$")
PATRON_CATALOGO = re.compile(r"^.{2,120}$")
PATRON_RUT = re.compile(r"^\d{7,8}-[\dkK]$")


def _validar(valor, patron, mensaje):
    if valor and not patron.match(valor):
        raise ValidationError(mensaje, code="formato_invalido")


def validar_nombre(valor):
    _validar(valor, PATRON_NOMBRE, "Solo letras, espacios, apóstrofes y guiones (2 a 60).")


def validar_direccion(valor):
    _validar(valor, PATRON_DIRECCION, "Dirección inválida (5 a 200 caracteres).")


def validar_comuna(valor):
    _validar(valor, PATRON_COMUNA, "Comuna inválida: solo letras (3 a 80).")


def validar_codigo(valor):
    _validar(valor, PATRON_CODIGO, "Código inválido: letras, números y guiones (2 a 40).")


def validar_catalogo(valor):
    _validar(valor, PATRON_CATALOGO, "Debe tener entre 2 y 120 caracteres.")


def validar_telefono(valor):
    digitos = re.sub(r"\D", "", valor or "")
    if valor and not PATRON_TELEFONO.match(digitos):
        raise ValidationError(
            "Teléfono inválido: entre 8 y 13 dígitos.", code="formato_invalido"
        )


def normalizar_rut(valor):
    """Deja el RUT en la forma canónica 12345678-9, sin puntos."""
    limpio = re.sub(r"[.\s]", "", (valor or "")).upper()
    if "-" not in limpio and len(limpio) > 1:
        limpio = limpio[:-1] + "-" + limpio[-1]
    return limpio


def _digito_verificador(cuerpo):
    suma = 0
    multiplicador = 2
    for digito in reversed(cuerpo):
        suma += int(digito) * multiplicador
        multiplicador = multiplicador + 1 if multiplicador < 7 else 2
    resto = 11 - (suma % 11)
    return {10: "K", 11: "0"}.get(resto, str(resto))


def validar_rut(valor):
    rut = normalizar_rut(valor)
    if not rut:
        return
    if not PATRON_RUT.match(rut):
        raise ValidationError("RUT inválido. Formato: 12345678-9.", code="formato_invalido")
    cuerpo, verificador = rut.split("-")
    if _digito_verificador(cuerpo) != verificador:
        raise ValidationError(
            "El dígito verificador del RUT no coincide.", code="dv_invalido"
        )
