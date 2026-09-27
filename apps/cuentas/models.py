from django.contrib.auth.models import User
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver

from apps.common.soft_delete import BorradoLogico


class Rol(BorradoLogico):
    nombre = models.CharField("nombre", max_length=60, unique=True)
    descripcion = models.CharField("descripción", max_length=200, blank=True)

    class Meta:
        verbose_name = "rol"
        verbose_name_plural = "roles"
        ordering = ["nombre"]

    def __str__(self):
        return self.nombre


class PerfilUsuario(models.Model):
    ACTIVO = "Activo"
    INACTIVO = "Inactivo"
    ESTADOS = [(ACTIVO, "Activo"), (INACTIVO, "Inactivo")]

    # Todas las referencias usan PROTECT. No estorba para el mantenedor,
    # porque Rol y Delegacion se dan de baja con borrado lógico y nunca se
    # borran de verdad. PROTECT queda como red de seguridad ante un DELETE
    # directo desde phpMyAdmin.
    usuario = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="perfil",
        verbose_name="usuario",
    )
    rol = models.ForeignKey(
        Rol,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="perfiles",
        verbose_name="rol",
    )
    delegacion = models.ForeignKey(
        "organizacion.Delegacion",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="perfiles",
        verbose_name="delegación",
    )
    estado = models.CharField(
        "estado", max_length=10, choices=ESTADOS, default=ACTIVO
    )

    class Meta:
        verbose_name = "perfil de usuario"
        verbose_name_plural = "perfiles de usuario"

    def __str__(self):
        return f"{self.usuario.get_full_name() or self.usuario.username} · {self.rol}"


@receiver(post_save, sender=User)
def crear_perfil(sender, instance, created, **kwargs):
    if created:
        PerfilUsuario.objects.create(usuario=instance)
