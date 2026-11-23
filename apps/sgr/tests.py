"""Pruebas de la Matriz SGR: cálculo puro, reglas del 4° trimestre y permisos."""

from datetime import timedelta
from decimal import Decimal

import pytest
from django.core.exceptions import ValidationError
from django.urls import reverse
from django.utils import timezone

from apps.sgr import calculos, servicios
from apps.sgr.models import (
    AjusteConducta,
    Area,
    Ausencia,
    Evidencia,
    Indicador,
    MetaIndicador,
    Periodo,
    RegistroGestion,
    Validacion,
)
from apps.sgr.validaciones import en_semana_actual, evaluar_puntaje, lunes_de, valor_conducta

pytestmark = pytest.mark.django_db


def test_el_porcentaje_se_recorta_en_el_tope():
    assert calculos.porcentaje(100, 100) == Decimal("1")
    assert calculos.porcentaje(150, 100) == Decimal("1.2")
    assert calculos.porcentaje(0, 100) == Decimal("0")
    assert calculos.porcentaje(10, 0) == Decimal("0")


def test_el_ponderado_multiplica_ponderador_por_porcentaje():
    assert calculos.ponderado(Decimal("0.2"), 150, 100) == Decimal("0.240")


def test_el_semaforo_usa_el_objetivo_al_dia():
    assert calculos.semaforo(Decimal("1.30"), Decimal("1.187")) == calculos.VERDE
    assert calculos.semaforo(Decimal("0.90"), Decimal("1.187")) == calculos.NARANJA
    assert calculos.semaforo(Decimal("0.70"), Decimal("1.187")) == calculos.ROJO


def test_el_total_ponderado_no_pasa_del_150():
    assert calculos.total_ponderado([Decimal("1.0"), Decimal("1.0")]) == Decimal("1.5")


def test_la_semana_cierra_el_lunes_siguiente():
    hoy = timezone.localdate()
    assert en_semana_actual(hoy, hoy) is True
    assert en_semana_actual(hoy - timedelta(days=8), hoy) is False
    assert lunes_de(hoy).weekday() == 0


def test_el_valor_de_la_conducta():
    assert valor_conducta("reclamo") == Decimal("-0.2")
    assert valor_conducta("felicitacion") == Decimal("0.1")


def _area():
    return Area.objects.create(nombre="Gestor Social 1", grupo="gestor-social")


def test_el_registro_no_supera_los_siete_del_dia(crear_usuario):
    usuario = crear_usuario("fun@test.cl", codigo="funcionario")
    area = _area()
    indicador = Indicador.objects.create(nombre="Visita terreno", grupo="gestor-social")
    hoy = timezone.localdate()
    for _ in range(7):
        RegistroGestion.objects.create(
            fecha=hoy, area=area, indicador=indicador, funcionario=usuario
        )
    octavo = RegistroGestion(
        fecha=hoy, area=area, indicador=indicador, funcionario=usuario
    )
    with pytest.raises(ValidationError):
        octavo.clean()


def test_el_registro_rechaza_una_semana_pasada(crear_usuario):
    usuario = crear_usuario("fun@test.cl", codigo="funcionario")
    area = _area()
    indicador = Indicador.objects.create(nombre="Operativo", grupo="gestor-social")
    registro = RegistroGestion(
        fecha=timezone.localdate() - timedelta(days=14),
        area=area,
        indicador=indicador,
        funcionario=usuario,
    )
    with pytest.raises(ValidationError):
        registro.clean()


def test_el_tablero_responde_al_admin(cliente, crear_usuario):
    admin = crear_usuario("admin@test.cl", codigo="admin")
    cliente.force_login(admin)
    assert cliente.get(reverse("sgr:tablero")).status_code == 200


def test_la_api_de_registros_escribe_solo_quien_corresponde(cliente, crear_usuario):
    admin = crear_usuario("admin@test.cl", codigo="admin")
    cliente.force_login(admin)
    assert cliente.get("/api/v1/sgr-records/").status_code == 200

    sin_lectura = crear_usuario("ver@test.cl", codigo="verificador")
    cliente.force_login(sin_lectura)
    assert cliente.get("/api/v1/sgr-records/").status_code == 403


def test_los_periodos_calculan_sus_dias():
    periodo = Periodo.objects.create(
        nombre="3er trimestre 2026",
        inicio=timezone.localdate(),
        termino=timezone.localdate() + timedelta(days=90),
    )
    assert periodo.dias_totales == 91


def test_regla_de_puntaje_del_correo():
    assert evaluar_puntaje("ejecutada", "externo", "Ana", "912345678")[0] is True
    assert evaluar_puntaje("preparatoria", "externo", "Ana", "912345678")[0] is False
    assert evaluar_puntaje("ejecutada", "delegado", "Ana", "912345678")[0] is False
    assert evaluar_puntaje("ejecutada", "externo", "", "")[0] is False


def test_el_registro_guarda_si_puntua(crear_usuario):
    usuario = crear_usuario("fun@test.cl", codigo="funcionario")
    area = _area()
    indicador = Indicador.objects.create(nombre="Atención", grupo="gestor-social")
    con_punto = RegistroGestion.objects.create(
        fecha=timezone.localdate(),
        area=area,
        indicador=indicador,
        funcionario=usuario,
        contacto_nombre="Ana",
        contacto_telefono="912345678",
    )
    assert con_punto.puntua is True
    sin_punto = RegistroGestion.objects.create(
        fecha=timezone.localdate(),
        area=area,
        indicador=indicador,
        funcionario=usuario,
        etapa="preparatoria",
        contacto_nombre="Ana",
        contacto_telefono="912345678",
    )
    assert sin_punto.puntua is False
    assert sin_punto.motivo_no_puntua


def test_un_periodo_cerrado_bloquea_el_registro(crear_usuario):
    usuario = crear_usuario("fun@test.cl", codigo="funcionario")
    area = _area()
    indicador = Indicador.objects.create(nombre="Atención", grupo="gestor-social")
    hoy = timezone.localdate()
    Periodo.objects.create(
        nombre="Trimestre cerrado",
        inicio=hoy - timedelta(days=5),
        termino=hoy + timedelta(days=5),
        situacion="cerrado",
    )
    registro = RegistroGestion(
        fecha=hoy, area=area, indicador=indicador, funcionario=usuario
    )
    with pytest.raises(ValidationError):
        registro.clean()


def test_los_topes_son_configurables_por_periodo():
    periodo = Periodo.objects.create(
        nombre="Trimestre con tope 150",
        inicio=timezone.localdate(),
        termino=timezone.localdate() + timedelta(days=90),
        tope_item=Decimal("1.5"),
    )
    assert calculos.porcentaje(200, 100, periodo.tope_item) == Decimal("1.5")


def test_la_validacion_no_la_puede_hacer_quien_registra(crear_usuario):
    autor = crear_usuario("fun@test.cl", codigo="funcionario")
    verificador = crear_usuario("ver@test.cl", codigo="verificador")
    area = _area()
    indicador = Indicador.objects.create(
        nombre="Con evidencia", grupo="gestor-social", requiere_evidencia=True
    )
    registro = RegistroGestion.objects.create(
        fecha=timezone.localdate(), area=area, indicador=indicador, funcionario=autor
    )
    evidencia = Evidencia.objects.create(
        registro=registro, vinculo="https://ejemplo.cl/foto", autor=autor
    )
    propia = Validacion(evidencia=evidencia, verificador=autor, decision="aprobada")
    with pytest.raises(ValidationError):
        propia.clean()

    Validacion.objects.create(
        evidencia=evidencia, verificador=verificador, decision="aprobada"
    )
    registro.refresh_from_db()
    evidencia.refresh_from_db()
    assert evidencia.estado_revision == "aprobada"
    assert registro.estado == "aprobada"


def test_la_ausencia_descuenta_la_meta_al_dia():
    area = _area()
    indicador = Indicador.objects.create(nombre="Atención", grupo="gestor-social")
    hoy = timezone.localdate()
    periodo = Periodo.objects.create(
        nombre="Período con ausencia",
        inicio=hoy - timedelta(days=30),
        termino=hoy + timedelta(days=30),
    )
    MetaIndicador.objects.create(
        periodo=periodo, area=area, indicador=indicador, ponderador=Decimal("1"), meta=100
    )
    sin_ausencia = servicios.resumen_area(periodo, area)
    Ausencia.objects.create(
        area=area,
        periodo=periodo,
        tipo="licencia",
        desde=hoy - timedelta(days=5),
        hasta=hoy,
    )
    con_ausencia = servicios.resumen_area(periodo, area)
    assert con_ausencia["esperado"] < sin_ausencia["esperado"]


def test_el_reclamo_toma_el_valor_del_cargo():
    from apps.organizacion.models import Cargo

    cargo = Cargo.objects.create(nombre="Apoyo Administrativo")
    area = Area.objects.create(nombre="AP 1", grupo="apoyo-administrativo", cargo=cargo)
    reclamo = AjusteConducta.objects.create(area=area, tipo="reclamo")
    assert reclamo.valor == Decimal("-0.30")
    assert valor_conducta("reclamo") == Decimal("-0.20")


def test_la_felicitacion_exige_respaldo():
    area = _area()
    sin_respaldo = AjusteConducta(area=area, tipo="felicitacion")
    with pytest.raises(ValidationError):
        sin_respaldo.clean()
    con_respaldo = AjusteConducta(area=area, tipo="felicitacion", respaldo="Oficio 12")
    con_respaldo.clean()


def test_el_resumen_marca_los_items_bajo_umbral():
    area = _area()
    indicador = Indicador.objects.create(nombre="Atención", grupo="gestor-social")
    hoy = timezone.localdate()
    periodo = Periodo.objects.create(
        nombre="Período en curso",
        inicio=hoy - timedelta(days=10),
        termino=hoy + timedelta(days=10),
    )
    MetaIndicador.objects.create(
        periodo=periodo, area=area, indicador=indicador, ponderador=Decimal("1"), meta=100
    )
    resumen = servicios.resumen_area(periodo, area)
    assert resumen["filas"][0]["bajo_umbral"] is True
    assert resumen["filas"][0]["en_tope"] is False


def test_el_generador_crea_alertas_de_tareas_vencidas(centro):
    from apps.sgr import alertas
    from apps.sgr.models import Alerta
    from apps.tubo.models import TareaTubo

    ayer = timezone.localdate() - timedelta(days=1)
    TareaTubo.objects.create(
        titulo="Atrasada", delegacion=centro, estado="pendiente", fecha_compromiso=ayer
    )
    assert alertas.generar_alertas() >= 1
    assert Alerta.todos.filter(tipo="tarea-vencida", resuelta=False).exists()
    assert alertas.generar_alertas() == 0


def test_la_edicion_rechaza_una_version_antigua(crear_usuario):
    from apps.sgr.forms import RegistroGestionForm

    usuario = crear_usuario("fun@test.cl", codigo="funcionario")
    area = _area()
    indicador = Indicador.objects.create(nombre="Atención", grupo="gestor-social")
    registro = RegistroGestion.objects.create(
        fecha=timezone.localdate(), area=area, indicador=indicador, funcionario=usuario
    )
    registro.refresh_from_db()
    version_vieja = registro.version
    registro.cantidad = 2
    registro.save()
    registro.refresh_from_db()
    assert registro.version == version_vieja + 1

    formulario = RegistroGestionForm(data={"version": version_vieja}, instance=registro)
    assert formulario.is_valid() is False
    assert "Otro usuario modificó" in str(formulario.errors)


def test_el_generador_marca_ingresos_sospechosos(crear_usuario):
    from apps.sgr import alertas
    from apps.sgr.models import Alerta

    usuario = crear_usuario("fun@test.cl", codigo="funcionario")
    area = _area()
    indicador = Indicador.objects.create(nombre="Atención", grupo="gestor-social")
    hoy = timezone.localdate()
    periodo = Periodo.objects.create(
        nombre="Período teléfono",
        inicio=hoy - timedelta(days=5),
        termino=hoy + timedelta(days=5),
    )
    for _ in range(5):
        RegistroGestion.objects.create(
            fecha=hoy,
            area=area,
            indicador=indicador,
            funcionario=usuario,
            contacto_nombre="Ana",
            contacto_telefono="+56900000000",
        )
    assert alertas.generar_alertas(periodo) >= 1
    assert Alerta.todos.filter(tipo="ingreso-sospechoso").exists()


# ------------------------------------------- Evidencia en el alta (mismo form)
def _datos_registro(usuario, area, indicador, **extra):
    datos = {
        "fecha": timezone.localdate().isoformat(),
        "area": area.pk,
        "indicador": indicador.pk,
        "funcionario": usuario.pk,
        "cantidad": 1,
        "etapa": "ejecutada",
        "tipo_solicitante": "externo",
        "estado": "registrada",
        "actividad": "visita",
    }
    datos.update(extra)
    return datos


def test_el_alta_exige_evidencia_si_el_indicador_la_requiere(crear_usuario):
    from apps.sgr.forms import RegistroGestionForm

    usuario = crear_usuario("fun@test.cl", codigo="funcionario")
    area = _area()
    indicador = Indicador.objects.create(
        nombre="Con evidencia", grupo="gestor-social", requiere_evidencia=True
    )
    formulario = RegistroGestionForm(data=_datos_registro(usuario, area, indicador))
    assert formulario.is_valid() is False
    assert "evidencia_archivo" in formulario.errors


def test_el_alta_web_crea_la_evidencia_en_la_misma_peticion(
    cliente, crear_usuario, settings, tmp_path
):
    from django.core.files.uploadedfile import SimpleUploadedFile

    settings.MEDIA_ROOT = tmp_path
    usuario = crear_usuario("fun@test.cl", codigo="funcionario")
    area = _area()
    indicador = Indicador.objects.create(
        nombre="Con evidencia", grupo="gestor-social", requiere_evidencia=True
    )
    cliente.force_login(usuario)
    archivo = SimpleUploadedFile("foto.png", b"contenido", content_type="image/png")
    respuesta = cliente.post(
        reverse("sgr:registros_nueva"),
        _datos_registro(
            usuario,
            area,
            indicador,
            contacto_nombre="Ana",
            contacto_telefono="912345678",
            evidencia_archivo=archivo,
            evidencia_tipo="foto",
        ),
    )
    assert respuesta.status_code == 302
    registro = RegistroGestion.objects.get()
    evidencia = Evidencia.objects.get()
    assert evidencia.registro == registro
    assert evidencia.autor == usuario
    assert evidencia.tipo == "foto"
    assert evidencia.estado_revision == "pendiente"


def test_la_api_crea_la_evidencia_con_el_registro(
    cliente, crear_usuario, settings, tmp_path
):
    from django.core.files.uploadedfile import SimpleUploadedFile

    settings.MEDIA_ROOT = tmp_path
    usuario = crear_usuario("fun@test.cl", codigo="funcionario")
    area = _area()
    indicador = Indicador.objects.create(
        nombre="Con evidencia", grupo="gestor-social", requiere_evidencia=True
    )
    cliente.force_login(usuario)
    archivo = SimpleUploadedFile("respaldo.pdf", b"%PDF-1.4", content_type="application/pdf")
    respuesta = cliente.post(
        "/api/v1/sgr-records/",
        {
            "date": timezone.localdate().isoformat(),
            "area": area.pk,
            "indicator": indicador.pk,
            "staff": usuario.pk,
            "quantity": 1,
            "stage": "ejecutada",
            "requester_type": "externo",
            "status": "registrada",
            "activity": "visita",
            "evidence_file": archivo,
            "evidence_kind": "informe",
        },
    )
    assert respuesta.status_code == 201
    evidencia = Evidencia.objects.get()
    assert evidencia.registro_id == respuesta.json()["id"]
    assert evidencia.autor == usuario


def test_la_api_rechaza_el_registro_sin_la_evidencia_exigida(cliente, crear_usuario):
    usuario = crear_usuario("fun@test.cl", codigo="funcionario")
    area = _area()
    indicador = Indicador.objects.create(
        nombre="Con evidencia", grupo="gestor-social", requiere_evidencia=True
    )
    cliente.force_login(usuario)
    respuesta = cliente.post(
        "/api/v1/sgr-records/",
        {
            "date": timezone.localdate().isoformat(),
            "area": area.pk,
            "indicator": indicador.pk,
            "staff": usuario.pk,
            "quantity": 1,
            "stage": "ejecutada",
            "requester_type": "externo",
            "status": "registrada",
            "activity": "visita",
        },
    )
    assert respuesta.status_code == 400
    assert not RegistroGestion.objects.exists()
