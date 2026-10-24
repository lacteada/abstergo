"""Pruebas del mantenedor de catálogos.

Comprueban que el formulario acota la delegación a las autorizadas y que los
campos código y estado se guardan.
"""

from types import SimpleNamespace

import pytest
from django.urls import reverse

from apps.catalogos.forms import MetaForm
from apps.catalogos.models import Meta

pytestmark = pytest.mark.django_db


def test_el_formulario_acota_la_delegacion_a_las_autorizadas(crear_usuario, centro, mar):
    """La regla se prueba en el formulario, que es donde vive.

    Hoy solo un rol global puede escribir metas, así que el acotamiento no se
    puede alcanzar por la vista: se verifica el `queryset` del campo, que es lo
    que rechaza una delegación no autorizada si la petición la altera.
    """
    usuario = crear_usuario(
        "delegado@test.cl", codigo="delegado", delegacion=centro, autorizadas=[centro]
    )

    formulario = MetaForm(request=SimpleNamespace(user=usuario, session={}))

    assert list(formulario.fields["delegacion"].queryset) == [centro]
    assert formulario.fields["delegacion"].initial == centro.pk
    assert mar not in formulario.fields["delegacion"].queryset


def test_crea_la_meta_derivando_el_codigo_del_nombre(cliente, crear_usuario, centro):
    """El alta no pide `codigo`: se deriva del nombre."""
    usuario = crear_usuario("admin@test.cl", codigo="admin", delegacion=centro)
    cliente.force_login(usuario)

    cliente.post(
        reverse("catalogos:metas_nueva"),
        {
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
