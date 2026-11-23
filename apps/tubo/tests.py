"""Pruebas del Tubo de trabajo: alta, kanban, cambio de estado e historial."""

from datetime import timedelta

import pytest
from django.urls import reverse
from django.utils import timezone

from apps.tubo.models import TareaTubo

pytestmark = pytest.mark.django_db


def test_la_tarea_deriva_su_referencia(centro):
    tarea = TareaTubo.objects.create(titulo="Reparar la plaza", delegacion=centro)
    assert tarea.referencia.startswith("TUB-")
    assert tarea.estado == "ingresada"


def test_el_delegado_ve_el_kanban_de_su_delegacion(cliente, crear_usuario, centro, mar):
    TareaTubo.objects.create(titulo="Tarea del Centro", delegacion=centro)
    TareaTubo.objects.create(titulo="Tarea del Mar", delegacion=mar)

    delegado = crear_usuario("del@test.cl", codigo="delegado", delegacion=centro)
    cliente.force_login(delegado)
    respuesta = cliente.get(reverse("tubo:tablero"))
    assert respuesta.status_code == 200
    contenido = respuesta.content.decode()
    assert "Tarea del Centro" in contenido
    assert "Tarea del Mar" not in contenido


def test_mover_cambia_el_estado_de_la_tarea(cliente, crear_usuario, centro):
    tarea = TareaTubo.objects.create(titulo="Tarea", delegacion=centro)
    delegado = crear_usuario("del@test.cl", codigo="delegado", delegacion=centro)
    cliente.force_login(delegado)
    respuesta = cliente.post(
        reverse("tubo:tareas_mover", args=[tarea.pk]), {"estado": "en_proceso"}
    )
    assert respuesta.status_code == 200
    assert respuesta.json()["estado"] == "en_proceso"
    tarea.refresh_from_db()
    assert tarea.estado == "en_proceso"
    assert tarea.historial.count() == 1


def test_mover_rechaza_una_transicion_no_permitida(cliente, crear_usuario, centro):
    tarea = TareaTubo.objects.create(titulo="Tarea", delegacion=centro)
    delegado = crear_usuario("del@test.cl", codigo="delegado", delegacion=centro)
    cliente.force_login(delegado)
    respuesta = cliente.post(
        reverse("tubo:tareas_mover", args=[tarea.pk]), {"estado": "realizada"}
    )
    assert respuesta.status_code == 400
    tarea.refresh_from_db()
    assert tarea.estado == "ingresada"


def test_la_tarea_vencida_se_marca(centro):
    ayer = timezone.localdate() - timedelta(days=1)
    tarea = TareaTubo.objects.create(
        titulo="Atrasada", delegacion=centro, estado="pendiente", fecha_compromiso=ayer
    )
    assert tarea.vencida is True
    assert tarea.dias_atraso == 1
    tarea.estado = "realizada"
    assert tarea.vencida is False


def test_la_api_de_tareas_responde_al_admin(cliente, crear_usuario):
    admin = crear_usuario("admin@test.cl", codigo="admin")
    cliente.force_login(admin)
    assert cliente.get("/api/v1/tasks/").status_code == 200

    consulta = crear_usuario("con@test.cl", codigo="consulta")
    cliente.force_login(consulta)
    assert cliente.get("/api/v1/tasks/").status_code == 403


def test_el_kanban_destaca_las_tareas_atrasadas(cliente, crear_usuario, centro):
    ayer = timezone.localdate() - timedelta(days=3)
    TareaTubo.objects.create(
        titulo="Reparar la plaza",
        delegacion=centro,
        estado="pendiente",
        fecha_compromiso=ayer,
    )
    delegado = crear_usuario("del@test.cl", codigo="delegado", delegacion=centro)
    cliente.force_login(delegado)

    respuesta = cliente.get(reverse("tubo:tablero"))

    assert respuesta.status_code == 200
    contenido = respuesta.content.decode()
    assert "kanban-tarjeta-atrasada" in contenido
    assert "Atrasada · 3 días" in contenido
    assert "1 atrasada" in contenido
