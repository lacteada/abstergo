from django.db import models

from apps.common.estados import ConEstado
from apps.common.soft_delete import BorradoLogico
from apps.common.validators import validar_catalogo, validar_codigo, validar_nombre


class Meta(ConEstado, BorradoLogico):
    codigo = models.SlugField(
        "código",
        max_length=40,
        unique=True,
        null=True,
        blank=True,
        validators=[validar_codigo],
    )
    nombre = models.CharField("nombre", max_length=120, validators=[validar_nombre])
    descripcion = models.CharField(
        "descripción", max_length=200, blank=True, validators=[validar_catalogo]
    )
    delegacion = models.ForeignKey(
        "organizacion.Delegacion",
        on_delete=models.PROTECT,
        related_name="metas",
        verbose_name="delegación",
    )

    class Meta:
        verbose_name = "meta"
        verbose_name_plural = "metas"
        ordering = ["delegacion", "nombre"]

    def __str__(self):
        return f"{self.nombre} ({self.delegacion})"


class TipoAtencion(ConEstado, BorradoLogico):
    codigo = models.SlugField(
        "código",
        max_length=40,
        unique=True,
        null=True,
        blank=True,
        validators=[validar_codigo],
    )
    nombre = models.CharField("nombre", max_length=120, validators=[validar_nombre])
    descripcion = models.CharField(
        "descripción", max_length=200, blank=True, validators=[validar_catalogo]
    )

    class Meta:
        verbose_name = "tipo de atención"
        verbose_name_plural = "tipos de atención"
        ordering = ["nombre"]

    def __str__(self):
        return self.nombre


class SubAtencion(ConEstado, BorradoLogico):
    codigo = models.SlugField(
        "código",
        max_length=40,
        unique=True,
        null=True,
        blank=True,
        validators=[validar_codigo],
    )
    nombre = models.CharField("nombre", max_length=120, validators=[validar_nombre])
    tipo_atencion = models.ForeignKey(
        TipoAtencion,
        on_delete=models.PROTECT,
        related_name="sub_atenciones",
        verbose_name="tipo de atención",
    )

    class Meta:
        verbose_name = "sub atención"
        verbose_name_plural = "sub atenciones"
        ordering = ["tipo_atencion", "nombre"]

    def __str__(self):
        return f"{self.nombre} ({self.tipo_atencion})"
