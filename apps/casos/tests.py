"""Pruebas de los casos sociales: hasta tres gestiones, reingreso y permisos."""

import pytest
from django.core.exceptions import ValidationError

from apps.casos.models import CasoSocial, GestionCaso, Llamada

pytestmark = pytest.mark.django_db


def _vecino(territorio):
    from apps.ciudadanos.models import Vecino

    return Vecino.objects.create(
        nombre="Ana Pérez",
        rut="11111111-1",
        telefono="+56911111111",
        territorio=territorio,
    )


def test_un_caso_admite_hasta_tres_gestiones(centro):
    caso = CasoSocial.objects.create(vecino=_vecino(centro), motivo="Ayuda social")
    for _ in range(3):
        GestionCaso.objects.create(caso=caso, detalle="Gestión")
    cuarta = GestionCaso(caso=caso, detalle="Cuarta")
    with pytest.raises(ValidationError):
        cuarta.clean()
    assert caso.gestiones_restantes == 0


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


def test_la_llamada_deriva_su_referencia(centro):
    llamada = Llamada.objects.create(vecino=_vecino(centro), motivo="Seguimiento")
    assert llamada.referencia.startswith("LLA-")
    assert llamada.estado == "pendiente"
