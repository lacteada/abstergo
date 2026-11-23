"""El paso manual al tubo desde una atención, una carta o una actividad.

Nada entra al tubo solo: estas fábricas crean el compromiso cuando alguien lo
pide con el botón. Son idempotentes: si el origen ya tiene su compromiso, lo
devuelven sin duplicar.
"""

from apps.tubo.models import TareaTubo


def desde_atencion(atencion, usuario):
    return TareaTubo.todos.get_or_create(
        atencion_id=atencion.pk,
        defaults={
            "titulo": f"{atencion.tipo_atencion.nombre} · {atencion.vecino.nombre}",
            "descripcion": atencion.motivo or "",
            "delegacion_id": atencion.delegacion_id,
            "tipo": "externo",
            "solicitante": atencion.vecino.nombre,
            "vecino_id": atencion.vecino_id,
            "responsable_id": atencion.funcionario_id or usuario.pk,
            "estado": "ingresada",
        },
    )


def desde_carta(carta, usuario):
    return TareaTubo.todos.get_or_create(
        carta_id=carta.pk,
        defaults={
            "titulo": f"Carta · {carta.asunto}",
            "descripcion": carta.observacion or "",
            "delegacion_id": carta.delegacion_id,
            "tipo": "interno",
            "solicitante": carta.remitente,
            "responsable_id": carta.encargado_id or usuario.pk,
            "estado": "ingresada",
        },
    )


def desde_registro(registro, usuario):
    """La actividad se enlaza por su propio campo `compromiso` (no un FK nuevo)."""
    if registro.compromiso_id:
        return registro.compromiso, False
    tarea = TareaTubo.todos.create(
        titulo=f"Actividad · {registro.indicador.nombre}",
        descripcion=registro.detalle or "",
        delegacion_id=registro.area.delegacion_id,
        tipo="interno",
        solicitante=registro.contacto_nombre,
        vecino_id=registro.vecino_id,
        responsable_id=registro.funcionario_id or usuario.pk,
        estado="ingresada",
    )
    # `update` directo para no disparar la evaluación de puntaje del registro.
    type(registro).objects.filter(pk=registro.pk).update(compromiso=tarea)
    registro.compromiso = tarea
    return tarea, True
