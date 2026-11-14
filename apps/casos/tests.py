"""Pruebas de los casos sociales: reingreso y permisos."""

import pytest
from django.core.exceptions import ValidationError

from apps.casos.models import CasoSocial

pytestmark = pytest.mark.django_db


def _vecino(territorio):
    from apps.ciudadanos.models import Vecino

    return Vecino.objects.create(
        nombre="Ana Pérez",
        rut="11111111-1",
        telefono="+56911111111",
        territorio=territorio,
    )


def test_el_reingreso_exige_el_caso_anterior(centro):
    reingreso = CasoSocial(
        vecino=_vecino(centro), motivo="Reingreso", reingreso=True
    )
    with pytest.raises(ValidationError):
        reingreso.clean()


def test_la_api_de_casos_responde_al_admin(cliente, crear_usuario):
    admin = crear_usuario("admin@test.cl", codigo="admin")
    cliente.force_login(admin)
    assert cliente.get("/api/v1/social-cases/").status_code == 200

    consulta = crear_usuario("con@test.cl", codigo="consulta")
    cliente.force_login(consulta)
    assert cliente.get("/api/v1/social-cases/").status_code == 403
