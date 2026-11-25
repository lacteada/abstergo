"""Criterios de aceptación de seguridad: web, Admin, API y ciclo de la credencial."""

import time
from datetime import timedelta

import pyotp
import pytest
from cryptography.fernet import Fernet
from django.contrib.auth.hashers import make_password
from django.test import Client
from django.utils import timezone
from rest_framework_simplejwt.tokens import RefreshToken

from apps.cuentas import mfa
from apps.cuentas.models import EventoAcceso, SegundoFactor

pytestmark = pytest.mark.django_db


@pytest.fixture(autouse=True)
def llave(settings):
    settings.MFA_ENCRYPTION_KEY = Fernet.generate_key().decode()


@pytest.fixture
def protegido(crear_usuario, centro):
    usuario = crear_usuario(delegacion=centro)
    secreto = pyotp.random_base32()
    factor = SegundoFactor.objects.create(
        usuario=usuario,
        activo=True,
        secreto_cifrado=mfa.cifrar(secreto),
        version=1,
        activado=timezone.now(),
        recuperaciones=[make_password("ABCD1234EF567890")],
    )
    return usuario, secreto, factor


def test_password_sola_no_crea_sesion_y_codigo_completa_acceso(protegido):
    usuario, secreto, _ = protegido
    cliente = Client()
    respuesta = cliente.post(
        "/login/?next=/tubo/cartas/",
        {
            "username": usuario.email,
            "password": "Clave.123",
        },
    )
    assert respuesta.url == "/login/segundo-factor/"
    assert "_auth_user_id" not in cliente.session
    assert cliente.get("/tubo/cartas/").status_code == 302
    respuesta = cliente.post("/login/segundo-factor/", {"codigo": pyotp.TOTP(secreto).now()})
    assert respuesta.url == "/tubo/cartas/"
    assert cliente.session["mfa_version"] == 1
    assert cliente.get("/tubo/cartas/").status_code == 200


def test_reutilizacion_totp_y_recuperacion_rechazada(protegido):
    usuario, secreto, factor = protegido
    codigo = pyotp.TOTP(secreto).now()
    assert mfa.verificar(usuario, codigo)
    assert not mfa.verificar(usuario, codigo)
    assert mfa.verificar(usuario, "ABCD1234EF567890")
    assert not mfa.verificar(usuario, "ABCD1234EF567890")
    factor.refresh_from_db()
    assert factor.recuperaciones == []


def test_bloqueo_persistente_tras_cinco_fallos(protegido):
    usuario, secreto, factor = protegido
    for _ in range(5):
        assert not mfa.verificar(usuario, "incorrecto")
    assert not mfa.verificar(usuario, pyotp.TOTP(secreto).now())
    factor.refresh_from_db()
    assert factor.bloqueado_hasta > timezone.now()
    factor.bloqueado_hasta = timezone.now() - timedelta(seconds=1)
    factor.save()
    assert mfa.verificar(usuario, pyotp.TOTP(secreto).now())


def test_codigo_vencido_y_desafio_vencido_no_autentican(protegido):
    usuario, secreto, _ = protegido
    assert not mfa.verificar(usuario, pyotp.TOTP(secreto).at(time.time() - 120))
    cliente = Client()
    cliente.post("/login/", {"username": usuario.email, "password": "Clave.123"})
    sesion = cliente.session
    datos = sesion["mfa_pendiente"]
    datos["inicio"] -= 301
    sesion["mfa_pendiente"] = datos
    sesion.save()
    assert (
        cliente.post("/login/segundo-factor/", {"codigo": pyotp.TOTP(secreto).now()}).url
        == "/login/"
    )
    assert "_auth_user_id" not in cliente.session


def test_cambio_password_o_cuenta_inactiva_invalida_desafio(protegido):
    usuario, secreto, _ = protegido
    cliente = Client()
    cliente.post("/login/", {"username": usuario.email, "password": "Clave.123"})
    usuario.set_password("Otra.Clave123")
    usuario.save()
    assert (
        cliente.post("/login/segundo-factor/", {"codigo": pyotp.TOTP(secreto).now()}).url
        == "/login/"
    )


def test_api_exige_otp_y_rechaza_tokens_previos(protegido):
    usuario, secreto, _ = protegido
    cliente = Client()
    anterior = RefreshToken.for_user(usuario)
    datos = {"email": usuario.email, "password": "Clave.123"}
    assert cliente.post("/api/v1/auth/login/", datos).status_code == 401
    assert (
        cliente.get(
            "/api/v1/auth/me/", HTTP_AUTHORIZATION=f"Bearer {anterior.access_token}"
        ).status_code
        == 401
    )
    assert cliente.post("/api/v1/auth/refresh/", {"refresh": str(anterior)}).status_code == 401
    datos["otp"] = pyotp.TOTP(secreto).now()
    respuesta = cliente.post("/api/v1/auth/login/", datos)
    assert respuesta.status_code == 200
    token = respuesta.json()["access"]
    assert cliente.get("/api/v1/auth/me/", HTTP_AUTHORIZATION=f"Bearer {token}").status_code == 200
    mfa.desactivar(usuario)
    assert cliente.get("/api/v1/auth/me/", HTTP_AUTHORIZATION=f"Bearer {token}").status_code == 401
    assert (
        cliente.post("/api/v1/auth/refresh/", {"refresh": respuesta.json()["refresh"]}).status_code
        == 401
    )


def test_sesiones_previas_y_admin_no_eluden_factor(protegido):
    usuario, _, _ = protegido
    cliente = Client()
    cliente.force_login(usuario)
    assert cliente.get("/").url == "/login/"
    cliente.force_login(usuario)
    assert cliente.get("/api/v1/auth/me/").status_code == 401
    assert cliente.get("/admin/login/").url == "/login/?next=/admin/"


def test_alta_exige_password_y_confirmacion_y_cifra_semilla(crear_usuario):
    usuario = crear_usuario()
    cliente = Client()
    cliente.force_login(usuario)
    respuesta = cliente.post("/perfil/seguridad/", {"accion": "preparar", "password": "mala"})
    assert "mfa_alta" not in cliente.session
    assert "no es válida" in respuesta.content.decode()
    cliente.post("/perfil/seguridad/", {"accion": "preparar", "password": "Clave.123"})
    pendiente = cliente.session["mfa_alta"]
    secreto = mfa.descifrar(pendiente["secreto"])
    assert secreto not in pendiente["secreto"]
    respuesta = cliente.post(
        "/perfil/seguridad/",
        {
            "accion": "confirmar",
            "codigo": pyotp.TOTP(secreto).now(),
        },
    )
    factor = SegundoFactor.objects.get(usuario=usuario)
    assert factor.activo and factor.version == 1
    assert secreto not in factor.secreto_cifrado
    assert len(factor.recuperaciones) == 8
    assert all(c.startswith("pbkdf2_") for c in factor.recuperaciones)
    assert "una sola vez" in respuesta.content.decode()
    assert "mfa_alta" not in cliente.session
    assert "no-store" in respuesta.headers["Cache-Control"]
    eventos = " ".join(EventoAcceso.objects.values_list("evento", flat=True))
    assert secreto not in eventos


def test_baja_requiere_password_y_codigo_y_revoca_sesiones(protegido):
    usuario, secreto, factor = protegido
    cliente = Client()
    cliente.force_login(usuario)
    sesion = cliente.session
    sesion["mfa_version"] = factor.version
    sesion.save()
    cliente.post(
        "/perfil/seguridad/", {"accion": "desactivar", "password": "Clave.123", "codigo": "malo"}
    )
    factor.refresh_from_db()
    assert factor.activo
    respuesta = cliente.post(
        "/perfil/seguridad/",
        {
            "accion": "desactivar",
            "password": "Clave.123",
            "codigo": pyotp.TOTP(secreto).now(),
        },
    )
    assert respuesta.status_code == 302
    factor.refresh_from_db()
    assert not factor.activo and not factor.secreto_cifrado and factor.version == 2


def test_redireccion_externa_no_permitida(protegido):
    usuario, secreto, _ = protegido
    cliente = Client()
    cliente.post(
        "/login/?next=https://ejemplo-malicioso.invalid",
        {
            "username": usuario.email,
            "password": "Clave.123",
        },
    )
    assert cliente.post("/login/segundo-factor/", {"codigo": pyotp.TOTP(secreto).now()}).url == "/"


def test_csrf_requerido_para_configuracion(crear_usuario):
    cliente = Client(enforce_csrf_checks=True)
    cliente.force_login(crear_usuario())
    assert (
        cliente.post(
            "/perfil/seguridad/", {"accion": "preparar", "password": "Clave.123"}
        ).status_code
        == 403
    )


def test_despliegue_rechaza_llave_ausente_o_invalida(settings):
    from apps.cuentas.checks import llave_mfa

    settings.MFA_ENCRYPTION_KEY = ""
    assert llave_mfa(None)[0].id == "cuentas.E001"
    settings.MFA_ENCRYPTION_KEY = "invalida"
    assert llave_mfa(None)
    settings.MFA_ENCRYPTION_KEY = Fernet.generate_key().decode()
    assert not llave_mfa(None)


def test_cambio_password_revoca_access_y_refresh(crear_usuario):
    usuario = crear_usuario()
    cliente = Client()
    respuesta = cliente.post(
        "/api/v1/auth/login/",
        {
            "email": usuario.email,
            "password": "Clave.123",
        },
    )
    tokens = respuesta.json()
    usuario.set_password("Clave.Nueva123")
    usuario.save()
    assert (
        cliente.get(
            "/api/v1/auth/me/",
            HTTP_AUTHORIZATION=f"Bearer {tokens['access']}",
        ).status_code
        == 401
    )
    assert cliente.post("/api/v1/auth/refresh/", {"refresh": tokens["refresh"]}).status_code == 401
