"""Invitación para activar la cuenta.

El administrador no define la contraseña: al crear la cuenta se le manda un
enlace firmado al correo. La persona entra, fija su contraseña y la cuenta
queda activa. El enlace sirve una sola vez: el token se firma con la
contraseña actual del usuario, así que al guardarla deja de valer.
"""

import logging

from django.conf import settings
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode

from apps.cuentas.models import Usuario

logger = logging.getLogger(__name__)


def enlace(usuario, request=None):
    """El enlace absoluto de activación, para el correo."""
    uid = urlsafe_base64_encode(force_bytes(usuario.pk))
    token = default_token_generator.make_token(usuario)
    ruta = reverse("cuentas:activar", args=[uid, token])
    return request.build_absolute_uri(ruta) if request else ruta


def usuario_de_enlace(uidb64):
    """El usuario del enlace, o None si el identificador no sirve."""
    try:
        pk = force_str(urlsafe_base64_decode(uidb64))
    except (TypeError, ValueError, OverflowError):
        return None
    return Usuario.vigentes().filter(pk=pk).first()


def enlace_valido(usuario, token):
    """¿El token corresponde al usuario y sigue vigente?"""
    return usuario is not None and default_token_generator.check_token(usuario, token)


def enviar(usuario, request=None):
    """Manda la invitación por correo. Devuelve True si salió.

    Un fallo se registra y se informa con False: el mantenedor avisa y ofrece
    reenviar, en vez de fingir que el correo salió.
    """
    contexto = {
        "nombre": usuario.first_name,
        "correo": usuario.email,
        "enlace": enlace(usuario, request),
        "dias": settings.INVITACION_DIAS,
    }
    try:
        send_mail(
            "Activa tu cuenta · Abstergo",
            render_to_string("correo/invitacion.txt", contexto),
            settings.DEFAULT_FROM_EMAIL,
            [usuario.email],
            html_message=render_to_string("correo/invitacion.html", contexto),
        )
    except Exception:
        logger.exception("No se pudo enviar la invitación a %s", usuario.email)
        return False
    return True
