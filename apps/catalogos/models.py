from django.db import models

from apps.common.soft_delete import BorradoLogico


class Meta(BorradoLogico):
    nombre = models.CharField("nombre", max_length=120)
    descripcion = models.CharField("descripción", max_length=200, blank=True)
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


class TipoAtencion(BorradoLogico):
    nombre = models.CharField("nombre", max_length=120)
    descripcion = models.CharField("descripción", max_length=200, blank=True)

    class Meta:
        verbose_name = "tipo de atención"
        verbose_name_plural = "tipos de atención"
        ordering = ["nombre"]

    def __str__(self):
        return self.nombre


class SubAtencion(BorradoLogico):
    nombre = models.CharField("nombre", max_length=120)
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
