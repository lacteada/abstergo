"""Pruebas del mantenedor de catálogos.

Comprueban que el formulario acota la delegación a las autorizadas y que los
campos código y estado se guardan.
"""

import pytest
from django.urls import reverse

from apps.catalogos.models import Meta

pytestmark = pytest.mark.django_db


def test_la_meta_acota_la_delegacion_a_las_autorizadas(
    cliente, crear_usuario, centro, mar
):
    usuario = crear_usuario(
        "delegado@test.cl", codigo="delegado", delegacion=centro, autorizadas=[centro]
    )
    cliente.force_login(usuario)

    respuesta = cliente.post(
        reverse("catalogos:metas_nueva"),
        {
            "codigo": "meta-x",
            "nombre": "Meta X",
            "descripcion": "",
            "delegacion": mar.pk,
            "estado": "activo",
        },
    )

    assert respuesta.status_code == 200  # vuelve con el error del formulario
    assert not Meta.objects.exists()


def test_crea_la_meta_con_codigo_y_estado(cliente, crear_usuario, centro):
    usuario = crear_usuario("admin@test.cl", codigo="admin", delegacion=centro)
    cliente.force_login(usuario)

    cliente.post(
        reverse("catalogos:metas_nueva"),
        {
            "codigo": "meta-x",
            "nombre": "Meta X",
            "descripcion": "",
            "delegacion": centro.pk,
            "estado": "inactivo",
        },
        follow=True,
    )

    meta = Meta.objects.get()
    assert meta.codigo == "meta-x"
    assert meta.estado == "inactivo"
