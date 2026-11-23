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


def test_una_atencion_crea_un_compromiso_en_el_tubo(crear_usuario, centro):
    """La atención pasa sola al tubo como compromiso de la delegación (RF-021)."""
    from apps.atenciones.models import Atencion
    from apps.catalogos.models import TipoAtencion
    from apps.ciudadanos.models import Vecino

    vecino = Vecino.objects.create(nombre="Ana", rut="11111111-1", territorio=centro)
    tipo = TipoAtencion.objects.create(nombre="Consulta")
    funcionario = crear_usuario("fun@test.cl", codigo="funcionario", delegacion=centro)

    atencion = Atencion.objects.create(
        vecino=vecino,
        tipo_atencion=tipo,
        delegacion=centro,
        funcionario=funcionario,
        motivo="Poda",
    )

    compromiso = TareaTubo.todos.get(atencion=atencion)
    assert compromiso.delegacion == centro
    assert compromiso.estado == "ingresada"
    assert compromiso.responsable == funcionario
    assert compromiso.vecino == vecino


def test_la_carta_se_desactiva_y_reactiva(cliente, crear_usuario, centro):
    from apps.tubo.models import Carta

    carta = Carta.objects.create(asunto="Oficio a la alcaldesa", delegacion=centro)
    delegado = crear_usuario("del@test.cl", codigo="delegado", delegacion=centro)
    cliente.force_login(delegado)

    cliente.post(reverse("tubo:cartas_desactivar", args=[carta.pk]))
    carta.refresh_from_db()
    assert carta.eliminado is not None

    cliente.post(reverse("tubo:cartas_reactivar", args=[carta.pk]))
    carta.refresh_from_db()
    assert carta.eliminado is None


def test_el_kanban_de_cartas_agrupa_por_estado(cliente, crear_usuario, centro):
    from apps.tubo.models import Carta

    Carta.objects.create(asunto="Oficio A", delegacion=centro, estado="en_proceso")
    delegado = crear_usuario("del@test.cl", codigo="delegado", delegacion=centro)
    cliente.force_login(delegado)

    respuesta = cliente.get(reverse("tubo:cartas_kanban"))

    assert respuesta.status_code == 200
    contenido = respuesta.content.decode()
    assert "data-kanban" in contenido
    assert "Oficio A" in contenido
    assert "En proceso" in contenido


def test_mover_una_carta_cambia_su_estado(cliente, crear_usuario, centro):
    from apps.tubo.models import Carta

    carta = Carta.objects.create(
        asunto="Oficio B", delegacion=centro, estado="en_proceso"
    )
    delegado = crear_usuario("del@test.cl", codigo="delegado", delegacion=centro)
    cliente.force_login(delegado)

    respuesta = cliente.post(
        reverse("tubo:cartas_mover", args=[carta.pk]), {"estado": "aprobada"}
    )

    assert respuesta.status_code == 200
    assert respuesta.json()["estado"] == "aprobada"
    carta.refresh_from_db()
    assert carta.estado == "aprobada"
