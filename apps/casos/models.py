"""Casos sociales: acompañamiento con hasta tres gestiones (RF-015/051/052).

Un caso se abre sobre un vecino, lleva hasta tres gestiones y puede reingresar
apuntando al caso anterior. El estado del caso no es la vigencia del registro,
así que no se usa `ConEstado`.
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

TIPOS_GESTION = [
    ("contacto", "Contacto"),
    ("visita", "Visita en terreno"),
    ("informe", "Informe"),
    ("derivacion", "Derivación"),
    ("otro", "Otro"),
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
    def gestiones_restantes(self):
        return max(0, MAX_GESTIONES - self.gestiones.count())


class GestionCaso(ConReferencia, BorradoLogico):
    """Una gestión de un caso social (contacto, visita, informe…)."""

    PREFIJO = "GCA"

    caso = models.ForeignKey(
        CasoSocial, on_delete=models.PROTECT, related_name="gestiones", verbose_name="caso"
    )
    fecha = models.DateField("fecha", default=timezone.localdate)
    tipo = models.CharField("tipo", max_length=12, choices=TIPOS_GESTION, default="contacto")
    hito = models.BooleanField("hito", default=False)
    plazo = models.DateField("plazo", null=True, blank=True)
    detalle = models.TextField("detalle", blank=True)

    class Meta:
        verbose_name = "gestión del caso"
        verbose_name_plural = "gestiones del caso"
        ordering = ["caso", "fecha"]

    def __str__(self):
        return f"{self.caso.referencia} · {self.get_tipo_display()} ({self.fecha})"

    def clean(self):
        if self.caso_id and self.pk is None and self.caso.gestiones.count() >= MAX_GESTIONES:
            raise ValidationError(
                {"caso": f"Un caso admite hasta {MAX_GESTIONES} gestiones."}
            )


class Llamada(ConReferencia, BorradoLogico):
    """Una llamada preventiva en la cola del gestor social (RF-050)."""

    PREFIJO = "LLA"

    ESTADOS = [
        ("pendiente", "Pendiente"),
        ("realizada", "Realizada"),
        ("no-contesta", "No contesta"),
        ("reagendada", "Reagendada"),
    ]

    vecino = models.ForeignKey(
        "ciudadanos.Vecino",
        on_delete=models.PROTECT,
        related_name="llamadas",
        verbose_name="vecino",
    )
    motivo = models.CharField("motivo", max_length=200, validators=[validar_texto])
    fecha_programada = models.DateField("fecha programada", default=timezone.localdate)
    estado = models.CharField("estado", max_length=12, choices=ESTADOS, default="pendiente")
    responsable = models.ForeignKey(
        "cuentas.Usuario",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="llamadas",
        verbose_name="responsable",
    )
    resultado = models.TextField("resultado", blank=True)

    class Meta:
        verbose_name = "llamada preventiva"
        verbose_name_plural = "llamadas preventivas"
        ordering = ["estado", "fecha_programada"]

    def __str__(self):
        return f"{self.referencia} · {self.vecino}"
