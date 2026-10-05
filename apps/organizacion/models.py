from django.db import models

from apps.common.soft_delete import BorradoLogico
from apps.common.validators import (
    validar_codigo,
    validar_comuna,
    validar_direccion,
    validar_nombre,
)


class Delegacion(BorradoLogico):
    codigo = models.CharField(
        "código", max_length=40, unique=True, validators=[validar_codigo]
    )
    nombre = models.CharField("nombre", max_length=120, validators=[validar_nombre])
    direccion = models.CharField(
        "dirección", max_length=200, blank=True, validators=[validar_direccion]
    )
    comuna = models.CharField(
        "comuna", max_length=80, blank=True, validators=[validar_comuna]
    )
    responsable = models.ForeignKey(
        "cuentas.Usuario",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="delegaciones_responsable",
        verbose_name="responsable",
    )

    class Meta:
        verbose_name = "delegación"
        verbose_name_plural = "delegaciones"
        ordering = ["nombre"]

    def __str__(self):
        return self.nombre
