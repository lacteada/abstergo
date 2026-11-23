"""Señales del tubo: la atención se refleja como compromiso en el kanban.

Cuando se registra una atención, nace un compromiso ligado a ella en el tubo de
la delegación, para que el trabajo no quede solo en el historial del vecino.
Es idempotente: usa la atención como llave, así no se duplica.
"""

from django.db.models.signals import post_save
from django.dispatch import receiver

from apps.atenciones.models import Atencion
from apps.tubo.models import TareaTubo


@receiver(post_save, sender=Atencion)
def crear_compromiso_desde_atencion(sender, instance, created, **kwargs):
    """Cada atención nueva deja un compromiso abierto en el tubo (RF-021)."""
    if not created:
        return
    TareaTubo.todos.get_or_create(
        atencion=instance,
        defaults={
            "titulo": f"{instance.tipo_atencion.nombre} · {instance.vecino.nombre}",
            "descripcion": instance.motivo or "",
            "delegacion": instance.delegacion,
            "tipo": "externo",
            "solicitante": instance.vecino.nombre,
            "vecino": instance.vecino,
            "responsable": instance.funcionario,
            "estado": "ingresada",
        },
    )
