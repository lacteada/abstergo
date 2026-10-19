"""Pruebas de la recuperación de contraseña."""

from datetime import timedelta

import pytest
from django.conf import settings
from django.contrib.auth import get_user_model
from django.utils import timezone

from apps.cuentas import otp
from apps.cuentas.models import RecuperacionPassword

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
