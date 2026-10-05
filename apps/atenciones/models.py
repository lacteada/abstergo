from django.db import models
from django.utils import timezone

from apps.common.soft_delete import BorradoLogico


class Atencion(BorradoLogico):
    """La atención entregada a un vecino.

    El historial de un vecino es la consulta de sus atenciones: no hay una
    tabla de historial aparte.
    """

    INGRESADA = "ingresada"
    EN_PROCESO = "en_proceso"
    CERRADA = "cerrada"
    DERIVADA = "derivada"
    ESTADOS = [
        (INGRESADA, "Ingresada"),
        (EN_PROCESO, "En proceso"),
        (CERRADA, "Cerrada"),
        (DERIVADA, "Derivada"),
    ]

    PRESENCIAL = "presencial"
    TELEFONO = "telefono"
    WEB = "web"
    CANALES = [
        (PRESENCIAL, "Presencial"),
        (TELEFONO, "Teléfono"),
        (WEB, "Web"),
    ]

    vecino = models.ForeignKey(
        "ciudadanos.Vecino",
        on_delete=models.PROTECT,
        related_name="atenciones",
        verbose_name="vecino",
    )
    tipo_atencion = models.ForeignKey(
        "catalogos.TipoAtencion",
        on_delete=models.PROTECT,
        related_name="atenciones",
        verbose_name="tipo de atención",
    )
    sub_atencion = models.ForeignKey(
        "catalogos.SubAtencion",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="atenciones",
        verbose_name="sub atención",
    )
    delegacion = models.ForeignKey(
        "organizacion.Delegacion",
        on_delete=models.PROTECT,
        related_name="atenciones",
        verbose_name="delegación",
    )
    funcionario = models.ForeignKey(
        "cuentas.Usuario",
        on_delete=models.PROTECT,
        related_name="atenciones",
        verbose_name="funcionario",
    )
    fecha = models.DateTimeField("fecha", default=timezone.now)
    motivo = models.CharField("motivo", max_length=200)
    detalle = models.TextField("detalle", blank=True)
    estado = models.CharField(
        "estado", max_length=20, choices=ESTADOS, default=INGRESADA
    )
    canal = models.CharField("canal", max_length=20, choices=CANALES, blank=True)

    class Meta:
        verbose_name = "atención"
        verbose_name_plural = "atenciones"
        ordering = ["-fecha"]

    def __str__(self):
        return f"Atención {self.pk} · {self.vecino} · {self.fecha:%d-%m-%Y}"
