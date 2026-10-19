"""Fixtures compartidas por las pruebas del sistema."""

import pytest
from django.contrib.auth import get_user_model
from django.test import Client

from apps.cuentas.models import Rol
from apps.organizacion.models import Delegacion

Usuario = get_user_model()


@pytest.fixture
def centro(db):
    return Delegacion.objects.create(
        codigo="centro", nombre="Centro", comuna="La Serena"
    )


@pytest.fixture
def mar(db):
    return Delegacion.objects.create(
        codigo="avenida-del-mar", nombre="Avenida del Mar", comuna="La Serena"
    )


@pytest.fixture
def crear_usuario(db):
    """Crea un usuario con su rol, delegación principal y autorizadas."""

    def _crear(
        email="u@test.cl",
        codigo="admin",
        delegacion=None,
        autorizadas=(),
        superuser=False,
    ):
        rol, _ = Rol.objects.get_or_create(
            codigo=codigo, defaults={"nombre": codigo.upper()}
        )
        usuario = Usuario.objects.create_user(
            email=email,
            password="Clave.123",
            rol=rol,
            delegacion=delegacion,
            is_superuser=superuser,
        )
        if autorizadas:
            usuario.delegaciones_autorizadas.set(autorizadas)
        return usuario

    return _crear


@pytest.fixture
def cliente():
    return Client()
