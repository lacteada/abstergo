from django.db import models

from apps.common.soft_delete import BorradoLogico


class Delegacion(BorradoLogico):
    codigo = models.CharField("código", max_length=40, unique=True)
    nombre = models.CharField("nombre", max_length=120)
    direccion = models.CharField("dirección", max_length=200, blank=True)
    comuna = models.CharField("comuna", max_length=80, blank=True)
    activo = models.BooleanField("activo", default=True)

    class Meta:
        verbose_name = "delegación"
        verbose_name_plural = "delegaciones"
        ordering = ["nombre"]

    def __str__(self):
        return self.nombre
