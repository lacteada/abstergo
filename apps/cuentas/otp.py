"""La recuperación de contraseña, en un solo lugar.

La web y la API llaman a estas tres funciones; el código vive siempre en la
tabla `RecuperacionPassword`, nunca en la sesión.
"""

import hmac
import logging

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils import timezone

from apps.cuentas.models import RecuperacionPassword

logger = logging.getLogger(__name__)
Usuario = get_user_model()

CODIGO_INVALIDO = "Código inválido o vencido."


def enviar_codigo(usuario, codigo):
    """Manda el código por correo. Un fallo se registra, no se esconde."""
    contexto = {
        "codigo": codigo,
        "nombre": usuario.first_name,
        "minutos": settings.OTP_EXPIRY_MINUTES,
    }
    try:
        send_mail(
            "Código para restablecer tu contraseña · Abstergo",
            render_to_string("correo/recuperacion.txt", contexto),
            settings.DEFAULT_FROM_EMAIL,
            [usuario.email],
            html_message=render_to_string("correo/recuperacion.html", contexto),
        )
    except Exception:
        logger.exception("No se pudo enviar el código a %s", usuario.email)


def _usuario(correo):
    return Usuario.vigentes().filter(email__iexact=correo).first()


def _vigente(correo, solo_validadas=False):
    """El usuario y su recuperación vigente más reciente."""
    usuario = _usuario(correo)
    if not usuario:
        return None, None
    consulta = RecuperacionPassword.objects.filter(usuario=usuario, usado__isnull=True)
    if solo_validadas:
        consulta = consulta.filter(validado__isnull=False)
    return usuario, consulta.order_by("-creado").first()


def solicitar(correo):
    """Genera y envía un código si el correo existe, y bloquea la cuenta.

    La respuesta es la misma exista o no la cuenta: no se revela qué correos hay.
    """
    usuario = _usuario(correo)
    if usuario:
        recuperacion = RecuperacionPassword.generar(usuario)
        enviar_codigo(usuario, recuperacion.codigo)
        # La cuenta queda bloqueada hasta que se fije la contraseña nueva.
        usuario.is_active = False
        usuario.save(update_fields=["is_active"])
    return usuario


def verificar(correo, codigo):
    """Marca el código como validado. Devuelve la lista de errores, o None."""
    _, recuperacion = _vigente(correo)
    if not recuperacion or not recuperacion.vigente():
        return [CODIGO_INVALIDO]
    if not hmac.compare_digest(recuperacion.codigo, codigo):
        recuperacion.intentos += 1
        recuperacion.save(update_fields=["intentos"])
        return [CODIGO_INVALIDO]
    recuperacion.validado = timezone.now()
    recuperacion.save(update_fields=["validado"])
    return None


def hay_codigo_validado(correo):
    """¿Ya se validó el código de ese correo?"""
    return _vigente(correo, solo_validadas=True)[1] is not None


def restablecer(correo, password, codigo=None):
    """Cambia la contraseña. Devuelve la lista de errores, o None.

    Con `codigo` exige que coincida; sin él, exige que ya se haya validado.
    """
    usuario, recuperacion = _vigente(correo, solo_validadas=codigo is None)
    if not recuperacion or not recuperacion.vigente():
        return [CODIGO_INVALIDO]
    if codigo is not None and not hmac.compare_digest(recuperacion.codigo, codigo):
        return [CODIGO_INVALIDO]
    try:
        validate_password(password, usuario)
    except ValidationError as error:
        return list(error.messages)
    usuario.set_password(password)
    # Con la contraseña nueva, la cuenta se reactiva.
    usuario.is_active = True
    usuario.save(update_fields=["password", "is_active"])
    recuperacion.usado = timezone.now()
    recuperacion.save(update_fields=["usado"])
    return None
