"""Pruebas del código visible autogenerado (`referencia`).

El código se deriva de la clave primaria, así que lo que hay que sostener es
que se genere solo, que no se repita y que no cambie nunca: es el identificador
que el PDF pide inmutable para las actividades.
"""

import pytest

from apps.atenciones.models import Atencion
from apps.catalogos.models import TipoAtencion
from apps.ciudadanos.models import Vecino
from apps.cuentas.models import Rol
from apps.organizacion.models import Delegacion

pytestmark = pytest.mark.django_db


@pytest.mark.parametrize(
    "crear, prefijo",
    [
        (lambda: Delegacion.objects.create(codigo="d1", nombre="Delegación Uno"), "DEL"),
        (lambda: Rol.objects.create(codigo="r1", nombre="Rol Uno"), "ROL"),
        (
            lambda: TipoAtencion.objects.create(codigo="t1", nombre="Tipo Uno"),
            "TIP",
        ),
    ],
)
def test_el_codigo_se_genera_con_su_prefijo(crear, prefijo):
    objeto = crear()
    assert objeto.referencia == f"{prefijo}-{objeto.pk:02d}"


def test_el_codigo_del_vecino_usa_su_prefijo(centro):
    vecino = Vecino.objects.create(nombre="Rosa Alvarado", rut="11111111-1", territorio=centro)
    assert vecino.referencia == f"VEC-{vecino.pk:02d}"


def test_el_codigo_de_la_atencion_usa_su_prefijo(centro, crear_usuario):
    vecino = Vecino.objects.create(nombre="Rosa", rut="11111111-1", territorio=centro)
    tipo = TipoAtencion.objects.create(codigo="t1", nombre="Tipo")
    usuario = crear_usuario("f@test.cl", codigo="funcionario", delegacion=centro)
    atencion = Atencion.objects.create(
        vecino=vecino,
        tipo_atencion=tipo,
        delegacion=centro,
        funcionario=usuario,
        motivo="Consulta",
    )
    assert atencion.referencia == f"AT-{atencion.pk:02d}"


def test_dos_registros_no_comparten_codigo():
    primera = Delegacion.objects.create(codigo="d1", nombre="Uno")
    segunda = Delegacion.objects.create(codigo="d2", nombre="Dos")
    assert primera.referencia != segunda.referencia


def test_el_codigo_no_cambia_al_guardar_de_nuevo():
    delegacion = Delegacion.objects.create(codigo="d1", nombre="Uno")
    original = delegacion.referencia

    delegacion.nombre = "Uno Renombrado"
    delegacion.save()

    delegacion.refresh_from_db()
    assert delegacion.referencia == original
