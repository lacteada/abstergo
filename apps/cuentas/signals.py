"""Señales que mantienen el espejo de grupos al día."""

from django.db.models.signals import post_save
from django.dispatch import receiver

from apps.cuentas.grupos import sincronizar, sincronizar_rol, sincronizar_usuario
from apps.cuentas.models import Rol, Usuario


def sincronizar_grupos(sender, **kwargs):
    """Corre tras migrar: deja un grupo por rol. La conecta `apps.py`."""
    sincronizar()


@receiver(post_save, sender=Rol)
def grupo_del_rol(sender, instance, **kwargs):
    sincronizar_rol(instance)


@receiver(post_save, sender=Usuario)
def grupo_del_usuario(sender, instance, **kwargs):
    sincronizar_usuario(instance)
