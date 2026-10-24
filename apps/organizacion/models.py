from django.db import models

from apps.common.codigo import ConCodigoDerivado
from apps.common.estados import ConEstado
from apps.common.referencia import ConReferencia
from apps.common.soft_delete import BorradoLogico
from apps.common.validators import (
    validar_codigo,
    validar_comuna,
    validar_direccion,
    validar_nombre,
)


class Delegacion(ConReferencia, ConCodigoDerivado, ConEstado, BorradoLogico):
    PREFIJO = "DEL"

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

    def esta_en_uso(self):
        """Verifica si la delegación tiene entidades activas vinculadas."""
        tiene_metas = self.metas.filter(eliminado__isnull=True).exists()
        tiene_vecinos = self.vecinos.filter(eliminado__isnull=True).exists()
        tiene_atenciones = self.atenciones.filter(eliminado__isnull=True).exists()
        tiene_usuarios = self.usuarios.filter(
            is_active=True, eliminado__isnull=True
        ).exists()
        return tiene_metas or tiene_vecinos or tiene_atenciones or tiene_usuarios

    def motivo_en_uso(self):
        detalles = []
        if self.usuarios.filter(is_active=True, eliminado__isnull=True).exists():
            detalles.append("usuarios activos")
        if self.vecinos.filter(eliminado__isnull=True).exists():
            detalles.append("vecinos")
        if self.metas.filter(eliminado__isnull=True).exists():
            detalles.append("metas")
        if self.atenciones.filter(eliminado__isnull=True).exists():
            detalles.append("atenciones")
        return f"La delegación está en uso por {', '.join(detalles)}."
