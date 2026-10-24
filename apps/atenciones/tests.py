"""Pruebas del flujo de ingreso de atención ciudadana.

Comprueban la dependencia tipo → sub atención, la delegación tomada del
contexto y el identificador que se muestra tras guardar.
"""

import pytest
from django.urls import reverse

from apps.atenciones.models import Atencion
from apps.catalogos.models import SubAtencion, TipoAtencion
from apps.ciudadanos.models import Vecino

pytestmark = pytest.mark.django_db


def _catalogos():
    orientacion = TipoAtencion.objects.create(
        codigo="orientacion", nombre="Orientación"
    )
    social = TipoAtencion.objects.create(codigo="social", nombre="Asistencia social")
    tramites = SubAtencion.objects.create(
        codigo="tramites", nombre="Trámites", tipo_atencion=orientacion
    )
    subsidio = SubAtencion.objects.create(
        codigo="subsidio", nombre="Subsidio", tipo_atencion=social
    )
    return orientacion, tramites, subsidio


def _vecino(territorio, rut="11111111-1", nombre="Rosa Alvarado"):
    return Vecino.objects.create(nombre=nombre, rut=rut, territorio=territorio)


def test_registra_la_atencion_y_muestra_el_identificador(cliente, crear_usuario, centro):
    orientacion, tramites, _ = _catalogos()
    vecino = _vecino(centro)
    usuario = crear_usuario("func@test.cl", codigo="funcionario", delegacion=centro)
    cliente.force_login(usuario)

    respuesta = cliente.post(
        reverse("atenciones:crear"),
        {
            "vecino": vecino.pk,
            "tipo_atencion": orientacion.pk,
            "sub_atencion": tramites.pk,
            "motivo": "Consulta de trámite",
            "estado": "ingresada",
            "canal": "presencial",
        },
        follow=True,
    )

    atencion = Atencion.objects.get()
    assert atencion.delegacion == centro
    assert atencion.funcionario == usuario
    assert atencion.referencia in respuesta.content.decode()


def test_rechaza_una_subatencion_de_otro_tipo(cliente, crear_usuario, centro):
    orientacion, _, subsidio = _catalogos()
    vecino = _vecino(centro)
    usuario = crear_usuario("func@test.cl", codigo="funcionario", delegacion=centro)
    cliente.force_login(usuario)

    respuesta = cliente.post(
        reverse("atenciones:crear"),
        {
            "vecino": vecino.pk,
            "tipo_atencion": orientacion.pk,
            "sub_atencion": subsidio.pk,
            "motivo": "Consulta",
            "estado": "ingresada",
        },
    )

    assert respuesta.status_code == 200
    assert not Atencion.objects.exists()
    assert "no pertenece al tipo" in respuesta.content.decode()


def test_la_delegacion_cae_al_territorio_si_no_hay_contexto(
    cliente, crear_usuario, centro
):
    orientacion, tramites, _ = _catalogos()
    vecino = _vecino(centro)
    # Un admin sin delegación activa: la atención usa el territorio del vecino.
    usuario = crear_usuario("admin@test.cl", codigo="admin", superuser=True)
    cliente.force_login(usuario)

    cliente.post(
        reverse("atenciones:crear"),
        {
            "vecino": vecino.pk,
            "tipo_atencion": orientacion.pk,
            "sub_atencion": tramites.pk,
            "motivo": "Consulta",
            "estado": "ingresada",
        },
    )

    assert Atencion.objects.get().delegacion == centro
