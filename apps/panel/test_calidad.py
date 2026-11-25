import json
from datetime import UTC, datetime

import pytest
from django.core import signing
from django.test import Client

from apps.panel.calidad import SALT

pytestmark = pytest.mark.django_db


def test_reporte_ausente_no_inventa_resultados(crear_usuario, settings, tmp_path):
    settings.QUALITY_REPORT_PATH = tmp_path / "inexistente.json"
    cliente = Client()
    cliente.force_login(crear_usuario())
    respuesta = cliente.get("/calidad/")
    assert respuesta.status_code == 200
    assert "Sin evidencia disponible" in respuesta.content.decode()
    assert cliente.get("/calidad/?descargar=1").status_code == 404


def test_solo_roles_autorizados_consultan_calidad(crear_usuario):
    cliente = Client()
    assert cliente.get("/calidad/").status_code == 302
    cliente.force_login(crear_usuario(codigo="funcionario"))
    assert cliente.get("/calidad/").status_code == 403
    assert cliente.get("/calidad/?descargar=1").status_code == 403


def test_firma_alteracion_y_fuente_distinta(crear_usuario, settings, tmp_path, monkeypatch):
    settings.QUALITY_REPORT_PATH = tmp_path / "calidad.json"
    reporte = {
        "fecha": datetime.now(UTC).isoformat(),
        "huella": "original",
        "revision": "abcdef1234567890",
        "entorno": "Pruebas",
        "correcto": True,
        "pruebas": {"total": 8, "fallos": 0, "errores": 0},
        "comprobaciones": [],
    }
    sobre = {"reporte": reporte, "firma": signing.dumps(reporte, salt=SALT)}
    settings.QUALITY_REPORT_PATH.write_text(json.dumps(sobre), encoding="utf-8")
    monkeypatch.setattr("apps.panel.calidad.huella_fuentes", lambda: "otra")
    cliente = Client()
    cliente.force_login(crear_usuario())
    assert "difiere del evaluado" in cliente.get("/calidad/").content.decode()
    assert cliente.get("/calidad/?descargar=1").json()["pruebas"]["total"] == 8
    sobre["reporte"]["pruebas"]["total"] = 999
    settings.QUALITY_REPORT_PATH.write_text(json.dumps(sobre), encoding="utf-8")
    assert "Sin evidencia disponible" in cliente.get("/calidad/").content.decode()


def test_sin_delegacion_no_accede_a_datos_territoriales(crear_usuario, centro):
    from apps.ciudadanos.models import Vecino

    cliente = Client()
    usuario = crear_usuario(codigo="funcionario")
    Vecino.objects.create(nombre="Vecino Protegido", rut="12345678-5", territorio=centro)
    cliente.force_login(usuario)
    respuesta = cliente.get("/vecinos/")
    assert "Vecino Protegido" not in respuesta.content.decode()
