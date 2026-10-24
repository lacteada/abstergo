"""Pruebas de las acciones sobre un registro del mantenedor.

Son las dos bajas más la vuelta atrás:

- **Desactivar**: siempre posible, reversible.
- **Eliminar**: borra la fila de verdad, y solo si nadie la usa.
- **Reactivar**: devuelve el registro a circulación.
"""

import pytest
from django.urls import reverse

from apps.atenciones.models import Atencion
from apps.catalogos.models import Meta, TipoAtencion
from apps.ciudadanos.models import Vecino
from apps.cuentas.models import Rol
from apps.organizacion.models import Delegacion

pytestmark = pytest.mark.django_db


def _admin(crear_usuario, **extra):
    extra.setdefault("superuser", True)
    return crear_usuario("admin@test.cl", codigo="admin", **extra)


def test_desactivar_es_posible_aunque_el_registro_este_en_uso(cliente, crear_usuario, centro):
    """La contracara de eliminar: nunca se bloquea."""
    Meta.objects.create(nombre="Meta de la delegación", delegacion=centro)
    cliente.force_login(_admin(crear_usuario))

    cliente.post(
        reverse("organizacion:delegaciones_desactivar", args=[centro.pk]), follow=True
    )

    centro.refresh_from_db()
    assert centro.eliminado is not None
    assert centro.estado == "inactivo"
    # La fila sigue en la base: es reversible.
    assert Delegacion.todos.filter(pk=centro.pk).exists()


def test_desactivar_deja_la_fila_visible_en_el_listado(cliente, crear_usuario, centro):
    cliente.force_login(_admin(crear_usuario))

    cliente.post(
        reverse("organizacion:delegaciones_desactivar", args=[centro.pk]), follow=True
    )

    respuesta = cliente.get(reverse("organizacion:delegaciones"))
    assert centro.referencia in respuesta.content.decode()


def test_reactivar_devuelve_el_registro_a_circulacion(cliente, crear_usuario, centro):
    cliente.force_login(_admin(crear_usuario))

    cliente.post(
        reverse("organizacion:delegaciones_desactivar", args=[centro.pk]), follow=True
    )
    cliente.post(
        reverse("organizacion:delegaciones_reactivar", args=[centro.pk]), follow=True
    )

    centro.refresh_from_db()
    assert centro.eliminado is None
    assert centro.estado == "activo"


def test_eliminar_se_bloquea_si_el_registro_esta_en_uso(cliente, crear_usuario, centro):
    Meta.objects.create(nombre="Meta de la delegación", delegacion=centro)
    cliente.force_login(_admin(crear_usuario))

    respuesta = cliente.post(
        reverse("organizacion:delegaciones_eliminar", args=[centro.pk]), follow=True
    )

    assert Delegacion.todos.filter(pk=centro.pk).exists(), "no debía borrarse"
    assert "No se puede eliminar" in respuesta.content.decode()


def test_eliminar_borra_la_fila_cuando_nadie_la_usa(cliente, crear_usuario, centro):
    libre = Delegacion.objects.create(nombre="Delegación Libre")
    cliente.force_login(_admin(crear_usuario))

    cliente.post(reverse("organizacion:delegaciones_eliminar", args=[libre.pk]), follow=True)

    assert not Delegacion.todos.filter(pk=libre.pk).exists(), "debía borrarse"


def test_eliminar_un_vecino_con_atenciones_avisa_en_vez_de_reventar(
    cliente, crear_usuario, centro
):
    """La base protege las referencias: el error se traduce, no se filtra."""
    vecino = Vecino.objects.create(nombre="Rosa Alvarado", rut="11111111-1", territorio=centro)
    tipo = TipoAtencion.objects.create(nombre="Orientación")
    administrador = _admin(crear_usuario)
    Atencion.objects.create(
        vecino=vecino,
        tipo_atencion=tipo,
        delegacion=centro,
        funcionario=administrador,
        motivo="Consulta",
    )
    cliente.force_login(administrador)

    respuesta = cliente.post(
        reverse("ciudadanos:vecinos_eliminar", args=[vecino.pk]), follow=True
    )

    assert respuesta.status_code == 200
    assert Vecino.todos.filter(pk=vecino.pk).exists(), "no debía borrarse"
    assert "No se puede eliminar" in respuesta.content.decode()


def test_desactivar_un_rol_sin_estado_solo_lo_marca(cliente, crear_usuario):
    """Un `Rol` no tiene estado binario: la baja es la marca de `eliminado`."""
    rol = Rol.objects.create(nombre="Rol Nuevo")
    cliente.force_login(_admin(crear_usuario))

    cliente.post(reverse("cuentas:roles_desactivar", args=[rol.pk]), follow=True)

    rol.refresh_from_db()
    assert rol.eliminado is not None
    assert rol.codigo == "rol-nuevo"
