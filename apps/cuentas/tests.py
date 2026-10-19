"""Pruebas de la recuperación de contraseña y de la invitación de cuentas."""

from datetime import timedelta

import pytest
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import default_token_generator
from django.core import mail
from django.urls import reverse
from django.utils import timezone
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode

from apps.cuentas import otp
from apps.cuentas.forms import UsuarioForm
from apps.cuentas.models import RecuperacionPassword, Rol

pytestmark = pytest.mark.django_db
Usuario = get_user_model()


@pytest.fixture
def usuario():
    return Usuario.objects.create_user(email="prueba@test.cl", password="Clave.123")


def test_un_correo_inexistente_no_crea_nada():
    assert otp.solicitar("nadie@test.cl") is None
    assert RecuperacionPassword.objects.count() == 0


def test_el_flujo_completo_cambia_la_contrasena(usuario):
    assert otp.solicitar(usuario.email) == usuario
    recuperacion = RecuperacionPassword.objects.get(usuario=usuario)

    assert otp.verificar(usuario.email, "000000") == [otp.CODIGO_INVALIDO]
    assert otp.verificar(usuario.email, recuperacion.codigo) is None
    assert otp.restablecer(usuario.email, "Otra.Clave.123") is None

    usuario.refresh_from_db()
    assert usuario.check_password("Otra.Clave.123")


def test_el_codigo_sirve_una_sola_vez(usuario):
    otp.solicitar(usuario.email)
    recuperacion = RecuperacionPassword.objects.get(usuario=usuario)
    otp.verificar(usuario.email, recuperacion.codigo)
    assert otp.restablecer(usuario.email, "Otra.Clave.123") is None
    assert otp.restablecer(usuario.email, "Tercera.Clave.123") == [otp.CODIGO_INVALIDO]


def test_vigentes_deja_fuera_los_dados_de_baja(usuario):
    usuario.eliminar()
    assert not Usuario.vigentes().filter(pk=usuario.pk).exists()
    assert Usuario.objects.filter(pk=usuario.pk).exists()


def test_el_reenvio_respeta_la_espera_minima(usuario):
    otp.solicitar(usuario.email)
    # Recién pedido el código, el reenvío espera en vez de emitir otro.
    assert otp.reenviar(usuario.email) > 0
    assert RecuperacionPassword.objects.filter(usuario=usuario).count() == 1


def test_el_reenvio_emite_tras_la_espera(usuario):
    otp.solicitar(usuario.email)
    primera = RecuperacionPassword.objects.get(usuario=usuario)
    primera.creado = timezone.now() - timedelta(
        seconds=settings.OTP_REENVIO_SEGUNDOS + 1
    )
    primera.save(update_fields=["creado"])
    assert otp.reenviar(usuario.email) == 0
    assert RecuperacionPassword.objects.filter(usuario=usuario).count() == 2


# ------------------------------------------------------- Invitar una cuenta
@pytest.fixture
def correos(settings):
    """Captura los correos salientes en `mail.outbox`."""
    settings.MAILERS = {
        "default": {"BACKEND": "django.core.mail.backends.locmem.EmailBackend"}
    }
    mail.outbox = []
    return mail.outbox


@pytest.fixture
def pendiente(db):
    """Una cuenta creada sin contraseña y sin acceso, como al invitarla."""
    usuario = Usuario.objects.create_user(email="pend@test.cl", password=None)
    usuario.is_active = False
    usuario.save(update_fields=["is_active"])
    return usuario


def _enlace(usuario):
    uid = urlsafe_base64_encode(force_bytes(usuario.pk))
    token = default_token_generator.make_token(usuario)
    return reverse("cuentas:activar", args=[uid, token])


def test_el_formulario_no_pide_contrasena():
    formulario = UsuarioForm()
    assert "clave" not in formulario.fields
    # Al crear, la cuenta nace pendiente: el estado se decide al activarla.
    assert "is_active" not in formulario.fields


def test_crear_usuario_manda_invitacion_y_queda_pendiente(
    cliente, crear_usuario, centro, correos
):
    admin = crear_usuario("admin@test.cl", codigo="admin", delegacion=centro)
    rol = Rol.objects.create(codigo="funcionario", nombre="FUNCIONARIO")
    cliente.force_login(admin)

    cliente.post(
        reverse("cuentas:usuarios_nueva"),
        {
            "email": "nuevo@test.cl",
            "nombre": "Nuevo",
            "apellido": "Usuario",
            "rol": rol.pk,
            "delegacion": centro.pk,
            "delegaciones_autorizadas": [],
        },
        follow=True,
    )

    usuario = Usuario.objects.get(email="nuevo@test.cl")
    assert usuario.pendiente
    assert usuario.is_active is False
    assert len(correos) == 1
    assert "/activar/" in correos[0].body


def test_activar_con_el_enlace_fija_la_clave(cliente, pendiente):
    respuesta = cliente.post(
        _enlace(pendiente),
        {"password1": "Clave.Nueva1", "password2": "Clave.Nueva1"},
    )

    pendiente.refresh_from_db()
    assert respuesta.status_code == 302
    assert pendiente.is_active is True
    assert pendiente.check_password("Clave.Nueva1")


def test_el_enlace_sirve_una_sola_vez(cliente, pendiente):
    url = _enlace(pendiente)
    cliente.post(url, {"password1": "Clave.Nueva1", "password2": "Clave.Nueva1"})

    # El token se firma con la contraseña: al fijarla, deja de valer.
    assert cliente.get(url).context["valido"] is False


def test_un_enlace_invalido_no_cambia_nada(cliente, pendiente):
    uid = urlsafe_base64_encode(force_bytes(pendiente.pk))
    respuesta = cliente.get(reverse("cuentas:activar", args=[uid, "token-malo"]))

    assert respuesta.context["valido"] is False
    pendiente.refresh_from_db()
    assert pendiente.pendiente


def test_reenviar_la_invitacion(cliente, crear_usuario, correos, pendiente):
    admin = crear_usuario("admin@test.cl", codigo="admin")
    cliente.force_login(admin)

    cliente.post(reverse("cuentas:usuarios_invitar", args=[pendiente.pk]), follow=True)

    assert len(correos) == 1
    assert "/activar/" in correos[0].body
