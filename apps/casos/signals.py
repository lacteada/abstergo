"""Señales de los casos: la atención genera su llamada preventiva (RF-050)."""

from django.db.models.signals import post_save
from django.dispatch import receiver

from apps.atenciones.models import Atencion
from apps.casos.models import Llamada


@receiver(post_save, sender=Atencion)
def crear_llamada_preventiva(sender, instance, created, **kwargs):
    """Cada atención registrada deja una llamada pendiente."""
    if created:
        Llamada.todos.get_or_create(
            atencion=instance,
            defaults={"vecino": instance.vecino, "motivo": instance.motivo},
        )
