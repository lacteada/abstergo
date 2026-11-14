"""Pruebas del registro de organizaciones comunitarias."""

import pytest
from django.core.management import call_command
from django.urls import reverse

from apps.comunidad.models import Organizacion

pytestmark = pytest.mark.django_db


def test_la_organizacion_deriva_codigo_y_referencia(centro):
    organizacion = Organizacion.objects.create(nombre="Junta de Vecinos Centro", territorio=centro)
    assert organizacion.codigo == "junta-de-vecinos-centro"
    assert organizacion.referencia.startswith("ORG-")


def test_el_listado_se_acota_a_la_delegacion_autorizada(cliente, crear_usuario, centro, mar):
    Organizacion.objects.create(nombre="Organizacion del Centro", territorio=centro)
    Organizacion.objects.create(nombre="Organizacion del Mar", territorio=mar)

    delegado = crear_usuario("del@test.cl", codigo="delegado", delegacion=centro)
    cliente.force_login(delegado)
    respuesta = cliente.get(reverse("comunidad:organizaciones"))
    assert respuesta.status_code == 200
    contenido = respuesta.content.decode()
    assert "Organizacion del Centro" in contenido
    assert "Organizacion del Mar" not in contenido


def test_la_api_reserva_community_organizations_para_quien_lee(cliente, crear_usuario):
    admin = crear_usuario("admin@test.cl", codigo="admin")
    cliente.force_login(admin)
    assert cliente.get("/api/v1/community-organizations/").status_code == 200

    consulta = crear_usuario("con@test.cl", codigo="consulta")
    cliente.force_login(consulta)
    assert cliente.get("/api/v1/community-organizations/").status_code == 403


def test_importar_jjvv_no_descarta_filas(tmp_path, centro):
    archivo = tmp_path / "jvvv.md"
    archivo.write_text(
        "| ORGANIZACIONES | DOMICILIO LEGAL | TERRIT. DELEG. | SOCIOS ACTIVOS | "
        "FECHA CONSTIT. | Nº REG. P.J. | FECHA INSCRIPC EN REG. | REG. DIR. Nº |\n"
        "|---|---|---|---|---|---|---|---|\n"
        "| JUNTA DE VECINOS CENTRO | CALLE 1 | CENTRO | 20 | 2020-01-01 | 123 | "
        "2020-01-02 | 999 |\n"
        "| AGRUPACION SIN TERRITORIO | CALLE 2 |  | x |  |  |  |  |\n",
        encoding="utf-8",
    )
    informe = tmp_path / "informe.md"
    call_command("importar_jjvv", archivo=str(archivo), informe=str(informe))

    assert Organizacion.todos.filter(nombre="JUNTA DE VECINOS CENTRO").exists()
    sin_territorio = Organizacion.todos.get(nombre="AGRUPACION SIN TERRITORIO")
    assert sin_territorio.territorio is None
    assert Organizacion.todos.count() == 2
    assert informe.exists()
    assert "Territorios vacíos: 1" in informe.read_text(encoding="utf-8")


def test_la_organizacion_sin_visita_se_detecta(centro):
    from apps.sgr import alertas
    from apps.sgr.models import Alerta

    organizacion = Organizacion.objects.create(nombre="Junta Sin Visita", territorio=centro)
    assert organizacion.ultima_visita is None
    assert organizacion.sin_visita is True
    assert alertas.generar_alertas() >= 1
    assert Alerta.todos.filter(tipo="organizacion-sin-visita").exists()


def test_la_exportacion_lleva_fecha_de_generacion(cliente, crear_usuario, centro):
    import io

    from openpyxl import load_workbook

    Organizacion.objects.create(nombre="Junta Export", territorio=centro)
    admin = crear_usuario("admin@test.cl", codigo="admin")
    cliente.force_login(admin)
    respuesta = cliente.get("/organizaciones/?exportar=1")
    assert respuesta.status_code == 200
    libro = load_workbook(io.BytesIO(respuesta.content))
    primera = libro.active.cell(row=1, column=1).value
    assert "generado el" in primera
