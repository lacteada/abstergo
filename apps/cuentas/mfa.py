"""Segundo factor común a la web y a la API, con bloqueo persistente y antirreutilización."""

import secrets
import time
from datetime import timedelta

import pyotp
from cryptography.fernet import Fernet, InvalidToken
from django.conf import settings
from django.contrib.auth.hashers import check_password, make_password
from django.core.exceptions import ImproperlyConfigured
from django.db import transaction
from django.utils import timezone

from apps.cuentas.models import EventoAcceso, SegundoFactor

ERROR_CODIGO = (
    "Código inválido, utilizado o vencido. Revisa tu autenticador o usa un código de recuperación."
)


def cifrador():
    try:
        return Fernet(settings.MFA_ENCRYPTION_KEY.encode())
    except (ValueError, AttributeError) as exc:
        raise ImproperlyConfigured("Configura MFA_ENCRYPTION_KEY con una llave Fernet.") from exc


def cifrar(secreto):
    return cifrador().encrypt(secreto.encode()).decode()


def descifrar(secreto):
    try:
        return cifrador().decrypt(secreto.encode()).decode()
    except InvalidToken as exc:
        raise ImproperlyConfigured(
            "La llave MFA no corresponde a las credenciales guardadas."
        ) from exc


def credencial(usuario):
    return SegundoFactor.objects.filter(usuario=usuario).first()


def evento(usuario, nombre):
    EventoAcceso.objects.create(usuario=usuario, evento=nombre)


def paso_valido(secreto, codigo, ultimo=-1):
    if len(codigo) != 6 or not codigo.isascii() or not codigo.isdigit():
        return None
    totp = pyotp.TOTP(secreto)
    paso = int(time.time()) // totp.interval
    for candidato in (paso, paso - 1, paso + 1):
        if candidato > ultimo and secrets.compare_digest(
            totp.at(candidato * totp.interval), codigo
        ):
            return candidato
    return None


@transaction.atomic
def verificar(usuario, codigo):
    """Consume una credencial una sola vez. El bloqueo rige también en DEBUG."""
    factor = SegundoFactor.objects.select_for_update().filter(usuario=usuario, activo=True).first()
    if not factor:
        return False
    ahora = timezone.now()
    if factor.bloqueado_hasta and factor.bloqueado_hasta > ahora:
        return False
    if factor.bloqueado_hasta:
        factor.fallos = 0
        factor.bloqueado_hasta = None
    codigo = codigo.strip().upper()
    paso = paso_valido(descifrar(factor.secreto_cifrado), codigo, factor.ultimo_paso)
    tipo = "Segundo factor verificado"
    aceptado = paso is not None
    if aceptado:
        # Comparación en UPDATE además del bloqueo: evita replays concurrentes en SQLite.
        aceptado = bool(
            SegundoFactor.objects.filter(
                pk=factor.pk,
                ultimo_paso=factor.ultimo_paso,
            ).update(ultimo_paso=paso)
        )
        factor.ultimo_paso = paso
    else:
        for indice, huella in enumerate(factor.recuperaciones):
            if check_password(codigo, huella):
                anteriores = factor.recuperaciones.copy()
                factor.recuperaciones.pop(indice)
                aceptado = bool(
                    SegundoFactor.objects.filter(
                        pk=factor.pk,
                        recuperaciones=anteriores,
                    ).update(recuperaciones=factor.recuperaciones)
                )
                tipo = "Código de recuperación consumido"
                break
    if aceptado:
        factor.fallos = 0
        factor.bloqueado_hasta = None
        evento(usuario, tipo)
    else:
        factor.fallos += 1
        if factor.fallos >= 5:
            factor.bloqueado_hasta = ahora + timedelta(minutes=5)
            evento(usuario, "Segundo factor bloqueado por intentos")
        else:
            evento(usuario, "Segundo factor rechazado")
    factor.save(update_fields=["fallos", "bloqueado_hasta"])
    return aceptado


@transaction.atomic
def activar(usuario, secreto, codigo):
    factor, _ = SegundoFactor.objects.select_for_update().get_or_create(usuario=usuario)
    if factor.activo:
        return None
    paso = paso_valido(secreto, codigo)
    if paso is None:
        return None
    codigos = [secrets.token_hex(8).upper() for _ in range(8)]
    factor.secreto_cifrado = cifrar(secreto)
    factor.recuperaciones = [make_password(c) for c in codigos]
    factor.activo = True
    factor.version += 1
    factor.ultimo_paso = paso
    factor.fallos = 0
    factor.bloqueado_hasta = None
    factor.activado = timezone.now()
    factor.save()
    evento(usuario, "Segundo factor activado")
    return codigos


@transaction.atomic
def desactivar(usuario):
    factor = SegundoFactor.objects.select_for_update().get(usuario=usuario)
    factor.activo = False
    factor.version += 1
    factor.secreto_cifrado = ""
    factor.recuperaciones = []
    factor.save()
    evento(usuario, "Segundo factor desactivado")


def version(usuario):
    factor = credencial(usuario)
    return factor.version if factor else 0


def marcar_sesion(request, usuario):
    request.session["mfa_version"] = version(usuario)
