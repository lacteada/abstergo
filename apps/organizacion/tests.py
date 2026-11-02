"""Pruebas del catálogo de Cargos y de su permiso por módulo."""

import pytest
from django.urls import reverse

from apps.organizacion.models import Cargo

pytestmark = pytest.mark.django_db


def test_el_cargo_deriva_codigo_y_referencia():
    cargo = Cargo.objects.create(nombre="Gestor Social")
    assert cargo.codigo == "gestor-social"
    assert cargo.referencia.startswith("CRG-")


def test_solo_el_admin_administra_los_cargos(cliente, crear_usuario):
    admin = crear_usuario("admin@test.cl", codigo="admin")
    cliente.force_login(admin)
    assert cliente.get(reverse("organizacion:cargos")).status_code == 200

    funcionario = crear_usuario("fun@test.cl", codigo="funcionario")
    cliente.force_login(funcionario)
    assert cliente.get(reverse("organizacion:cargos")).status_code == 403


def test_la_api_reserva_positions_al_admin(cliente, crear_usuario):
    admin = crear_usuario("admin@test.cl", codigo="admin")
    cliente.force_login(admin)
    assert cliente.get("/api/v1/positions/").status_code == 200

    consulta = crear_usuario("con@test.cl", codigo="consulta")
    cliente.force_login(consulta)
    assert cliente.get("/api/v1/positions/").status_code == 403
