"""Modelo del Tubo de trabajo: las tareas de una delegación, tipo kanban.

Cada tarea tiene un estado (las columnas del tablero) y un funcionario
responsable. El estado es el ciclo de vida de la tarea, no la vigencia del
registro, así que no se usa `ConEstado` (igual que en `Atencion`).
"""

from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone

from apps.common.referencia import ConReferencia
from apps.common.soft_delete import BorradoLogico
from apps.common.validators import validar_texto

# Las columnas del kanban, en orden.
ESTADOS = [
    ("ingresada", "Ingresada"),
    ("pendiente", "Pendiente"),
    ("en_proceso", "En proceso"),
    ("realizada", "Realizada"),
]

TIPOS = [("externo", "Externo"), ("interno", "Interno")]

# Transiciones permitidas entre estados (RF-018).
TRANSICIONES = {
    "ingresada": {"pendiente", "en_proceso"},
    "pendiente": {"ingresada", "en_proceso"},
    "en_proceso": {"pendiente", "realizada"},
    "realizada": {"en_proceso"},
}


class TareaTubo(ConReferencia, BorradoLogico):
    """Una tarea del tubo de trabajo de la delegación."""

    PREFIJO = "TUB"

    titulo = models.CharField("título", max_length=160, validators=[validar_texto])
    descripcion = models.TextField("descripción", blank=True)
    estado = models.CharField(
        "estado", max_length=12, choices=ESTADOS, default="ingresada"
    )
    delegacion = models.ForeignKey(
        "organizacion.Delegacion",
        on_delete=models.PROTECT,
        related_name="tareas_tubo",
        verbose_name="delegación",
    )
    territorio = models.ForeignKey(
        "organizacion.Territorio",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="tareas_tubo",
        verbose_name="territorio (sector)",
    )
    tipo = models.CharField("tipo", max_length=8, choices=TIPOS, default="externo")
    solicitante = models.CharField("solicitante", max_length=160, blank=True)
    responsable = models.ForeignKey(
        "cuentas.Usuario",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="tareas_tubo",
        verbose_name="funcionario responsable",
    )
    apoyo = models.ForeignKey(
        "cuentas.Usuario",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="tareas_apoyo",
        verbose_name="apoyo",
    )
    vecino = models.ForeignKey(
        "ciudadanos.Vecino",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="tareas_tubo",
        verbose_name="vecino",
    )
    atencion = models.ForeignKey(
        "atenciones.Atencion",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="compromisos",
        verbose_name="atención de origen",
    )
    avance = models.PositiveIntegerField("avance (%)", default=0)
    fecha_ingreso = models.DateTimeField("fecha de ingreso", default=timezone.now)
    fecha_compromiso = models.DateField("fecha de compromiso", null=True, blank=True)
    orden = models.PositiveIntegerField("orden", default=0)

    class Meta:
        verbose_name = "compromiso"
        verbose_name_plural = "compromisos"
        ordering = ["orden", "-fecha_ingreso"]

    def __str__(self):
        return self.titulo

    def clean(self):
        # Sin responsable ni fecha no se guarda (RF-017).
        if not self.responsable_id:
            raise ValidationError(
                {"responsable": "Toda tarea necesita un funcionario responsable."}
            )
        if not self.fecha_compromiso:
            raise ValidationError(
                {"fecha_compromiso": "Toda tarea necesita una fecha de compromiso."}
            )

    def puede_pasar_a(self, estado):
        """Si el cambio de estado respeta las transiciones permitidas."""
        return estado == self.estado or estado in TRANSICIONES.get(self.estado, set())

    @property
    def vencida(self):
        """Si la fecha de compromiso ya pasó y la tarea sigue abierta (RF-019)."""
        if not self.fecha_compromiso or self.estado == "realizada":
            return False
        return self.fecha_compromiso < timezone.localdate()

    @property
    def dias_atraso(self):
        if not self.vencida:
            return 0
        return (timezone.localdate() - self.fecha_compromiso).days

    def save(self, *args, **kwargs):
        anterior = None
        if self.pk:
            anterior = (
                type(self)
                .objects.filter(pk=self.pk)
                .values_list("estado", flat=True)
                .first()
            )
        super().save(*args, **kwargs)
        if anterior is not None and anterior != self.estado:
            HistorialEstado.objects.create(
                tarea=self,
                anterior=anterior,
                estado=self.estado,
                usuario=getattr(self, "_usuario_cambio", None),
            )


class HistorialEstado(ConReferencia, BorradoLogico):
    """El registro de cada cambio de estado de una tarea (RF-018)."""

    PREFIJO = "HIS"

    tarea = models.ForeignKey(
        TareaTubo, on_delete=models.PROTECT, related_name="historial", verbose_name="tarea"
    )
    anterior = models.CharField("estado anterior", max_length=12, choices=ESTADOS)
    estado = models.CharField("estado nuevo", max_length=12, choices=ESTADOS)
    usuario = models.ForeignKey(
        "cuentas.Usuario",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="historial_tubo",
        verbose_name="usuario",
    )
    fecha = models.DateTimeField("fecha", default=timezone.now)
    motivo = models.CharField("motivo", max_length=200, blank=True)

    class Meta:
        verbose_name = "cambio de estado"
        verbose_name_plural = "cambios de estado"
        ordering = ["-fecha"]

    def __str__(self):
        return f"{self.tarea} · {self.anterior} → {self.estado}"


class Carta(ConReferencia, BorradoLogico):
    """Correspondencia con su seguimiento (RF-054)."""

    PREFIJO = "CAR"

    ESTADOS = [
        ("en_proceso", "En proceso"),
        ("aprobada", "Aprobada"),
        ("finalizada", "Finalizada"),
        ("no_aplica", "No aplica"),
    ]
    DESTINATARIOS = [("alcaldesa", "Alcaldesa"), ("delegado", "Delegado")]

    asunto = models.CharField("asunto", max_length=200, validators=[validar_texto])
    correlativo = models.PositiveIntegerField("correlativo", null=True, blank=True)
    destinatario = models.CharField(
        "destinatario", max_length=10, choices=DESTINATARIOS, default="delegado"
    )
    remitente = models.CharField("remitente", max_length=160, blank=True)
    contacto = models.CharField("contacto", max_length=120, blank=True)
    fecha = models.DateField("fecha", default=timezone.localdate)
    encargado = models.ForeignKey(
        "cuentas.Usuario",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="cartas",
        verbose_name="encargado de seguimiento",
    )
    delegacion = models.ForeignKey(
        "organizacion.Delegacion",
        on_delete=models.PROTECT,
        related_name="cartas",
        verbose_name="delegación",
    )
    estado = models.CharField(
        "estado", max_length=12, choices=ESTADOS, default="en_proceso"
    )
    observacion = models.TextField("observación", blank=True)

    class Meta:
        verbose_name = "carta"
        verbose_name_plural = "cartas"
        ordering = ["-fecha", "-pk"]

    def __str__(self):
        return f"{self.referencia} · {self.asunto}"
