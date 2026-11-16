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


def test_la_atencion_genera_llamada_preventiva(centro, crear_usuario):
    from apps.atenciones.models import Atencion
    from apps.casos.models import Llamada
    from apps.catalogos.models import TipoAtencion

    vecino = _vecino(centro)
    tipo = TipoAtencion.objects.create(nombre="Consulta")
    funcionario = crear_usuario("fun@test.cl", codigo="funcionario", delegacion=centro)
    Atencion.objects.create(
        vecino=vecino,
        tipo_atencion=tipo,
        delegacion=centro,
        funcionario=funcionario,
        motivo="Poda",
    )
    llamada = Llamada.objects.get(vecino=vecino)
    assert llamada.estado == "pendiente"


def test_cerrar_una_llamada_preventiva(cliente, crear_usuario, centro):
    from django.urls import reverse

    from apps.casos.models import Llamada

    vecino = _vecino(centro)
    llamada = Llamada.objects.create(vecino=vecino, motivo="Poda")
    delegado = crear_usuario("del@test.cl", codigo="delegado", delegacion=centro)
    cliente.force_login(delegado)

    respuesta = cliente.post(reverse("casos:llamadas_cerrar", args=[llamada.pk]))

    assert respuesta.status_code == 302
    llamada.refresh_from_db()
    assert llamada.estado == "realizada"
    assert llamada.realizada_por == delegado
