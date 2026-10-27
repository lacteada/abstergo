"""La recuperación de contraseña, en un solo lugar.

La web y la API llaman a estas funciones; el código vive siempre en la
tabla `RecuperacionPassword`, nunca en la sesión. Un mismo registro se cierra
por dos vías: el código de 6 dígitos o el enlace firmado del correo. La que se
use primero anula la otra.
"""

import hmac
import logging

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core import signing
from django.core.exceptions import ValidationError
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils import timezone
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode

from apps.cuentas.models import RecuperacionPassword

logger = logging.getLogger(__name__)
Usuario = get_user_model()

CODIGO_INVALIDO = "Código inválido o vencido."
# Sal propio: el token del enlace de recuperación no vale para la invitación.
SAL_ENLACE = "cuentas.recuperacion"


def enlace(usuario, recuperacion, request=None):
    """El enlace absoluto para restablecer sin digitar el código.

    El token firma la clave del registro: no se puede inventar ni reusar en
    otra recuperación, y vence con el registro, igual que el código.
    """
    token = signing.dumps(recuperacion.pk, salt=SAL_ENLACE)
    uid = urlsafe_base64_encode(force_bytes(usuario.pk))
    ruta = reverse("cuentas:recuperar_enlace", args=[uid, token])
    return request.build_absolute_uri(ruta) if request else ruta


def enviar_codigo(usuario, recuperacion, request=None):
    """Manda el correo con el código y el enlace. Un fallo se registra, no se esconde."""
    contexto = {
        "codigo": recuperacion.codigo,
        "nombre": usuario.first_name,
        "minutos": settings.OTP_EXPIRY_MINUTES,
        "enlace": enlace(usuario, recuperacion, request),
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


def solicitar(correo, request=None):
    """Genera y envía un código si el correo existe, y bloquea la cuenta.

    La respuesta es la misma exista o no la cuenta: no se revela qué correos hay.
    """
    usuario = _usuario(correo)
    if usuario:
        recuperacion = RecuperacionPassword.generar(usuario)
        enviar_codigo(usuario, recuperacion, request)
        # La cuenta queda bloqueada hasta que se fije la contraseña nueva.
        usuario.is_active = False
        usuario.save(update_fields=["is_active"])
    return usuario


def reenviar(correo, request=None):
    """Genera y envía un código nuevo, respetando la espera mínima.

    Devuelve los segundos que faltan para poder reenviar, o 0 si se envió. El
    límite de frecuencia evita el uso del reenvío como vector de spam o de
    fuerza bruta sobre el correo de un tercero.
    """
    usuario = _usuario(correo)
    if not usuario:
        return 0
    ultima = (
        RecuperacionPassword.objects.filter(usuario=usuario)
        .order_by("-creado")
        .first()
    )
    if ultima:
        transcurrido = (timezone.now() - ultima.creado).total_seconds()
        espera = settings.OTP_REENVIO_SEGUNDOS
        if transcurrido < espera:
            return int(espera - transcurrido) + 1
    recuperacion = RecuperacionPassword.generar(usuario)
    enviar_codigo(usuario, recuperacion, request)
    return 0


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


def recuperacion_de_enlace(uidb64, token):
    """El usuario y el registro de un enlace, o `(None, None)`.

    El enlace sirve solo mientras el registro sea el vigente y nadie lo haya
    cerrado por la otra vía: si el código se validó, el enlace queda muerto.
    """
    try:
        pk = force_str(urlsafe_base64_decode(uidb64))
        usuario = Usuario.vigentes().filter(pk=pk).first()
    except (TypeError, ValueError, OverflowError):
        return None, None
    if not usuario:
        return None, None
    try:
        # El vencimiento real manda por el registro; este tope es solo refuerzo.
        recuperacion_pk = signing.loads(
            token, salt=SAL_ENLACE, max_age=settings.OTP_EXPIRY_MINUTES * 60
        )
    except signing.BadSignature:
        return None, None
    _, vigente = _vigente(usuario.email)
    recuperacion = RecuperacionPassword.objects.filter(
        pk=recuperacion_pk, usuario=usuario
    ).first()
    if (
        not recuperacion
        or vigente is None
        or recuperacion.pk != vigente.pk
        or not recuperacion.vigente()
        or recuperacion.validado is not None
    ):
        return None, None
    return usuario, recuperacion


def _aplicar(usuario, recuperacion, password):
    """Fija la contraseña nueva y cierra el registro. Devuelve errores o None."""
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


def restablecer(correo, password, codigo=None):
    """Cambia la contraseña. Devuelve la lista de errores, o None.

    Con `codigo` exige que coincida; sin él, exige que ya se haya validado.
    """
    usuario, recuperacion = _vigente(correo, solo_validadas=codigo is None)
    if not recuperacion or not recuperacion.vigente():
        return [CODIGO_INVALIDO]
    if codigo is not None and not hmac.compare_digest(recuperacion.codigo, codigo):
        return [CODIGO_INVALIDO]
    return _aplicar(usuario, recuperacion, password)


def restablecer_enlace(usuario, recuperacion, password):
    """Cierra la recuperación por el enlace: fija la clave y marca el registro.

    Deja el código sin valor: el registro queda `usado`, así que `verificar`
    ya no lo acepta.
    """
    if not recuperacion.vigente() or recuperacion.validado is not None:
        return [CODIGO_INVALIDO]
    return _aplicar(usuario, recuperacion, password)
