"""Pruebas del cambio de delegación activa.

El selector de contexto debe actualizar el alcance y rechazar una delegación
que el perfil no tiene autorizada.
"""

import pytest
from django.urls import reverse

from apps.ciudadanos.models import Vecino
from apps.organizacion.models import Delegacion

pytestmark = pytest.mark.django_db


def _vecino(nombre, rut, territorio):
    return Vecino.objects.create(nombre=nombre, rut=rut, territorio=territorio)


def test_cambiar_delegacion_actualiza_el_alcance(cliente, crear_usuario, centro, mar):
    _vecino("Ana Centro", "11111111-1", centro)
    _vecino("Beto Mar", "12222222-5", mar)
    usuario = crear_usuario(
        "delegado@test.cl",
        codigo="delegado",
        delegacion=centro,
        autorizadas=[centro, mar],
    )
    cliente.force_login(usuario)

    inicial = cliente.get(reverse("ciudadanos:vecinos")).context["object_list"]
    assert [v.nombre for v in inicial] == ["Ana Centro"]

    cliente.post(reverse("panel:cambiar_delegacion"), {"delegacion": mar.pk})

    nombres = [
        v.nombre
        for v in cliente.get(reverse("ciudadanos:vecinos")).context["object_list"]
    ]
    assert nombres == ["Beto Mar"]


def test_rechaza_una_delegacion_no_autorizada(cliente, crear_usuario, centro, mar):
    rural = Delegacion.objects.create(codigo="rural", nombre="Rural")
    _vecino("Ana Centro", "11111111-1", centro)
    _vecino("Beto Mar", "12222222-5", mar)
    _vecino("Cami Rural", "13333333-9", rural)
    usuario = crear_usuario(
        "delegado@test.cl", codigo="delegado", delegacion=centro, autorizadas=[centro]
    )
    cliente.force_login(usuario)

    cliente.post(reverse("panel:cambiar_delegacion"), {"delegacion": rural.pk})

    # Se queda en su delegación principal (centro).
    nombres = [
        v.nombre
        for v in cliente.get(reverse("ciudadanos:vecinos")).context["object_list"]
    ]
    assert nombres == ["Ana Centro"]
