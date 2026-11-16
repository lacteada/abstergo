"""Pruebas básicas de la API v1 que no cubren las apps de dominio."""

import pytest

pytestmark = pytest.mark.django_db


def test_login_y_me(cliente, crear_usuario):
    crear_usuario("admin@test.cl", codigo="admin")

    respuesta = cliente.post(
        "/api/v1/auth/login/", {"email": "admin@test.cl", "password": "Clave.123"}
    )

    assert respuesta.status_code == 200
    token = respuesta.json()["access"]
    perfil = cliente.get(
        "/api/v1/auth/me/", HTTP_AUTHORIZATION=f"Bearer {token}"
    )
    assert perfil.status_code == 200
    assert perfil.json()["role_code"] == "admin"


def test_sin_token_da_401(cliente):
    assert cliente.get("/api/v1/neighbors/").status_code == 401


def test_credenciales_invalidas_dan_401(cliente, crear_usuario):
    crear_usuario("admin@test.cl", codigo="admin")
    respuesta = cliente.post(
        "/api/v1/auth/login/", {"email": "admin@test.cl", "password": "mala"}
    )
    assert respuesta.status_code == 401
