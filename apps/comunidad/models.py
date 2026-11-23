from django.db import models
from django.utils import timezone

from apps.common.codigo import ConCodigoDerivado
from apps.common.estados import ConEstado
from apps.common.referencia import ConReferencia
from apps.common.soft_delete import BorradoLogico
from apps.common.validators import (
    validar_catalogo,
    validar_codigo,
    validar_direccion,
    validar_texto,
)

# Meses sin visita a partir de los cuales se avisa (RF-060).
MESES_SIN_VISITA = 6

TIPOS_ORGANIZACION = [
    ("territorial", "Territorial"),
    ("funcional", "Funcional"),
]

SUBTIPOS_ORGANIZACION = [
    ("adulto-mayor", "Adulto mayor"),
    ("deportiva", "Deportiva"),
    ("centro-madres-cultural-juvenil", "Centro de madres, cultural o juvenil"),
    ("comite", "Comité de vecinos, allegados o seguridad"),
    ("otro", "Otro"),
]

SITUACIONES_ORGANIZACION = [
    ("vigente", "Vigente"),
    ("inactiva", "Inactiva"),
    ("cerrada", "Cerrada"),
]

VERIFICACIONES = [
    ("sin-verificar", "Sin verificar"),
    ("verificada", "Verificada"),
]


class Organizacion(ConReferencia, ConCodigoDerivado, ConEstado, BorradoLogico):
    """Una junta de vecinos o agrupación comunitaria (registro OROC).

    Los campos siguen la base de JJVV y agrupaciones de la Municipalidad:
    domicilio legal, territorio (delegación), socios activos y los datos del
    registro de personalidad jurídica. Varias columnas admiten vacío porque el
    origen las trae incompletas.
    """

    PREFIJO = "ORG"

    codigo = models.CharField(
        "código", max_length=40, unique=True, validators=[validar_codigo]
    )
    nombre = models.CharField("nombre", max_length=200, validators=[validar_texto])
    domicilio_legal = models.CharField(
        "domicilio legal", max_length=200, blank=True, validators=[validar_direccion]
    )
    territorio = models.ForeignKey(
        "organizacion.Delegacion",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="organizaciones",
        verbose_name="territorio",
    )
    tipo = models.CharField(
        "tipo", max_length=12, choices=TIPOS_ORGANIZACION, blank=True
    )
    subtipo = models.CharField(
        "subtipo", max_length=30, choices=SUBTIPOS_ORGANIZACION, blank=True
    )
    situacion = models.CharField(
        "situación", max_length=10, choices=SITUACIONES_ORGANIZACION, default="vigente"
    )
    verificacion = models.CharField(
        "verificación", max_length=14, choices=VERIFICACIONES, default="sin-verificar"
    )
    socios_activos = models.PositiveIntegerField(
        "socios activos", null=True, blank=True
    )
    fecha_constitucion = models.DateField(
        "fecha de constitución", null=True, blank=True
    )
    registro_pj = models.CharField(
        "N° registro P.J.", max_length=20, blank=True, validators=[validar_catalogo]
    )
    fecha_inscripcion = models.DateField(
        "fecha de inscripción", null=True, blank=True
    )
    registro_dir = models.CharField(
        "N° registro directorio", max_length=20, blank=True, validators=[validar_catalogo]
    )
    # Directiva de la organización (OROC): quién la preside y administra.
    presidente = models.CharField("presidente", max_length=120, blank=True)
    tesorero = models.CharField("tesorero", max_length=120, blank=True)
    secretario = models.CharField("secretario", max_length=120, blank=True)

    class Meta:
        verbose_name = "organización comunitaria"
        verbose_name_plural = "organizaciones comunitarias"
        ordering = ["nombre"]

    def __str__(self):
        return self.nombre

    @property
    def ultima_visita(self):
        """La fecha de la última visita registrada a la organización (RF-059)."""
        return (
            self.registros_sgr.filter(actividad="visita")
            .order_by("-fecha")
            .values_list("fecha", flat=True)
            .first()
        )

    @property
    def sin_visita(self):
        """Si la organización lleva demasiado sin una visita (RF-060)."""
        ultima = self.ultima_visita
        if not ultima:
            return True
        return (timezone.localdate() - ultima).days > MESES_SIN_VISITA * 30
