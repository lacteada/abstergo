"""Casos sociales: agrupan hasta tres atenciones del mismo vecino (RF-015).

Un caso se abre sobre un vecino y puede reingresar apuntando al caso anterior.
La atención es la gestión del caso; no hay una tabla de gestiones aparte.
"""

from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone

from apps.common.referencia import ConReferencia
from apps.common.soft_delete import BorradoLogico
from apps.common.validators import validar_texto

ESTADOS = [
    ("abierto", "Abierto"),
    ("seguimiento", "En seguimiento"),
    ("cerrado", "Cerrado"),
]

MAX_GESTIONES = 3


class CasoSocial(ConReferencia, BorradoLogico):
    """Un caso de acompañamiento social sobre un vecino."""

    PREFIJO = "CAS"

    vecino = models.ForeignKey(
        "ciudadanos.Vecino",
        on_delete=models.PROTECT,
        related_name="casos",
        verbose_name="vecino",
    )
    responsable = models.ForeignKey(
        "cuentas.Usuario",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="casos",
        verbose_name="responsable",
    )
    fecha_apertura = models.DateField("fecha de apertura", default=timezone.localdate)
    motivo = models.CharField("motivo", max_length=200, validators=[validar_texto])
    estado = models.CharField("estado", max_length=12, choices=ESTADOS, default="abierto")
    reingreso = models.BooleanField("es reingreso", default=False)
    caso_anterior = models.ForeignKey(
        "self",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="reingresos",
        verbose_name="caso anterior",
    )
    observaciones = models.TextField("observaciones", blank=True)

    class Meta:
        verbose_name = "caso social"
        verbose_name_plural = "casos sociales"
        ordering = ["-fecha_apertura"]

    def __str__(self):
        return f"{self.referencia} · {self.vecino}"

    def clean(self):
        if self.reingreso and not self.caso_anterior_id:
            raise ValidationError(
                {"caso_anterior": "Un reingreso debe indicar el caso anterior."}
            )

    @property
    def atenciones_restantes(self):
        return max(0, MAX_GESTIONES - self.atenciones.count())


class Llamada(ConReferencia, BorradoLogico):
    """Llamada preventiva que deja cada atención (RF-050).

    Al registrar una atención nace una llamada pendiente; al ejecutarla se
    cierra. Es la cola de seguimiento del apoyo administrativo.
    """

    PREFIJO = "LLA"

    PENDIENTE = "pendiente"
    REALIZADA = "realizada"
    ANULADA = "anulada"
    ESTADOS = [
        (PENDIENTE, "Pendiente"),
        (REALIZADA, "Realizada"),
        (ANULADA, "Anulada"),
    ]

    vecino = models.ForeignKey(
        "ciudadanos.Vecino",
        on_delete=models.PROTECT,
        related_name="llamadas",
        verbose_name="vecino",
    )
    atencion = models.ForeignKey(
        "atenciones.Atencion",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="llamadas",
        verbose_name="atención de origen",
    )
    motivo = models.CharField("motivo", max_length=200, blank=True)
    fecha_programada = models.DateField("fecha programada", null=True, blank=True)
    estado = models.CharField(
        "estado", max_length=10, choices=ESTADOS, default=PENDIENTE
    )
    fecha_realizada = models.DateTimeField("fecha realizada", null=True, blank=True)
    realizada_por = models.ForeignKey(
        "cuentas.Usuario",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="llamadas_realizadas",
        verbose_name="realizada por",
    )

    class Meta:
        verbose_name = "llamada preventiva"
        verbose_name_plural = "llamadas preventivas"
        ordering = ["estado", "fecha_programada"]

    def __str__(self):
        return f"{self.referencia} · {self.vecino}"

    @property
    def pendiente(self):
        return self.estado == self.PENDIENTE
