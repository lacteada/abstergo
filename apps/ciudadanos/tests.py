"""Pruebas del generador de vecinos de relleno."""

import pytest
from django.core.management import call_command

from apps.ciudadanos.models import Vecino
from apps.common.validators import validar_rut
from apps.organizacion.models import Delegacion

pytestmark = pytest.mark.django_db


@pytest.fixture
def territorio(db):
    return Delegacion.objects.create(
        codigo="centro", nombre="Centro", comuna="La Serena"
    )


def test_genera_vecinos_con_rut_valido_y_unico(territorio):
    call_command("generar_vecinos", cantidad=25)

    vecinos = list(Vecino.objects.all())
    assert len(vecinos) == 25
    for vecino in vecinos:
        # No levanta si el dígito verificador está bien; es la misma regla del
        # formulario.
        validar_rut(vecino.rut)
    assert len({vecino.rut for vecino in vecinos}) == 25


def test_volver_a_correrlo_no_duplica(territorio):
    call_command("generar_vecinos", cantidad=10)
    call_command("generar_vecinos", cantidad=10)

    assert Vecino.objects.count() == 10
