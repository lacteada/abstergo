"""Pruebas de las tablas de cumplimiento (Ley 21.719)."""

from datetime import timedelta

import pytest
from django.test import RequestFactory
from django.utils import timezone

from apps.cumplimiento.auditoria import registrar
from apps.cumplimiento.models import RegistroAuditoria, SolicitudTitular

pytestmark = pytest.mark.django_db


def _vecino(territorio):
    from apps.ciudadanos.models import Vecino

    return Vecino.objects.create(nombre="Ana Pérez", rut="11111111-1", territorio=territorio)


def test_la_solicitud_tiene_plazo_de_30_dias(centro):
    hoy = timezone.localdate()
    solicitud = SolicitudTitular.objects.create(
        vecino=_vecino(centro), tipo=SolicitudTitular.ACCESO, fecha_solicitud=hoy
    )
    assert solicitud.fecha_limite == hoy + timedelta(days=30)


def test_la_bitacora_registra_una_escritura(centro):
    peticion = RequestFactory().post("/")
    peticion.user = None
    registrar(peticion, "crear", None, "Alta de prueba")
    assert RegistroAuditoria.objects.filter(accion="crear").exists()
