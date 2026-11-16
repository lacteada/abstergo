"""Pruebas del tubo de cartas (RF-054)."""

import pytest

from apps.tubo.models import Carta

pytestmark = pytest.mark.django_db


def test_la_carta_deriva_su_referencia(centro):
    carta = Carta.objects.create(asunto="Solicitud de poda", delegacion=centro)
    assert carta.referencia.startswith("CAR-")
    assert carta.estado == "en_proceso"


def test_el_listado_de_cartas_muestra_totales_por_estatus(cliente, crear_usuario, centro):
    from django.urls import reverse

    Carta.objects.create(asunto="A", delegacion=centro, estado="en_proceso")
    Carta.objects.create(asunto="B", delegacion=centro, estado="finalizada")
    delegado = crear_usuario("del@test.cl", codigo="delegado", delegacion=centro)
    cliente.force_login(delegado)

    respuesta = cliente.get(reverse("tubo:cartas"))

    assert respuesta.status_code == 200
    contenido = respuesta.content.decode()
    assert "En proceso: 1" in contenido
    assert "Finalizada: 1" in contenido
