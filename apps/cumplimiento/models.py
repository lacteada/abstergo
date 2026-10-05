from datetime import timedelta

from django.db import models
from django.utils import timezone

from apps.common.soft_delete import BorradoLogico


BASES_LICITUD = [
    ("deber_legal", "Cumplimiento de un deber legal"),
    ("funcion_publica", "Ejercicio de funciones públicas"),
    ("interes_vital", "Interés vital del titular"),
    ("consentimiento", "Consentimiento del titular"),
]

CATEGORIAS_DATOS = [
    ("identificacion", "Identificación"),
    ("contacto", "Contacto"),
    ("socioeconomico", "Socioeconómico (sensible)"),
    ("salud", "Salud (sensible)"),
]


class ActividadTratamiento(BorradoLogico):
    """Registro de actividades de tratamiento (RAT) que exige la ley."""

    nombre = models.CharField("nombre", max_length=120)
    finalidad = models.CharField("finalidad", max_length=200)
    base_licitud = models.CharField(
        "base de licitud", max_length=20, choices=BASES_LICITUD, default="deber_legal"
    )
    categorias_datos = models.CharField("categorías de datos", max_length=200)
    destinatarios = models.CharField("destinatarios", max_length=200, blank=True)
    plazo_conservacion_dias = models.PositiveIntegerField(
        "plazo de conservación (días)", null=True, blank=True
    )
    medidas_seguridad = models.CharField("medidas de seguridad", max_length=200, blank=True)
    responsable = models.ForeignKey(
        "cuentas.Usuario",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="actividades_tratamiento",
        verbose_name="responsable",
    )

    class Meta:
        verbose_name = "actividad de tratamiento"
        verbose_name_plural = "actividades de tratamiento"
        ordering = ["nombre"]

    def __str__(self):
        return self.nombre


class SolicitudTitular(BorradoLogico):
    """Solicitud de un titular para ejercer sus derechos (ARCOP + bloqueo)."""

    ACCESO = "acceso"
    RECTIFICACION = "rectificacion"
    SUPRESION = "supresion"
    OPOSICION = "oposicion"
    PORTABILIDAD = "portabilidad"
    BLOQUEO = "bloqueo"
    TIPOS = [
        (ACCESO, "Acceso"),
        (RECTIFICACION, "Rectificación"),
        (SUPRESION, "Supresión"),
        (OPOSICION, "Oposición"),
        (PORTABILIDAD, "Portabilidad"),
        (BLOQUEO, "Bloqueo temporal"),
    ]

    INGRESADA = "ingresada"
    EN_PROCESO = "en_proceso"
    RESPONDIDA = "respondida"
    RECHAZADA = "rechazada"
    ESTADOS = [
        (INGRESADA, "Ingresada"),
        (EN_PROCESO, "En proceso"),
        (RESPONDIDA, "Respondida"),
        (RECHAZADA, "Rechazada"),
    ]

    vecino = models.ForeignKey(
        "ciudadanos.Vecino",
        on_delete=models.PROTECT,
        related_name="solicitudes",
        verbose_name="titular",
    )
    tipo = models.CharField("tipo", max_length=20, choices=TIPOS)
    estado = models.CharField(
        "estado", max_length=20, choices=ESTADOS, default=INGRESADA
    )
    fecha_solicitud = models.DateField("fecha de solicitud", default=timezone.localdate)
    fecha_limite = models.DateField("fecha límite", null=True, blank=True)
    fecha_respuesta = models.DateField("fecha de respuesta", null=True, blank=True)
    detalle = models.TextField("detalle", blank=True)
    respondido_por = models.ForeignKey(
        "cuentas.Usuario",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="solicitudes_respondidas",
        verbose_name="respondido por",
    )

    class Meta:
        verbose_name = "solicitud del titular"
        verbose_name_plural = "solicitudes del titular"
        ordering = ["-fecha_solicitud"]

    def save(self, *args, **kwargs):
        # El plazo legal de respuesta es de 30 días corridos.
        if self.fecha_limite is None and self.fecha_solicitud is not None:
            self.fecha_limite = self.fecha_solicitud + timedelta(days=30)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.get_tipo_display()} · {self.vecino}"


class IncidenteSeguridad(BorradoLogico):
    """Vulneración de seguridad y su notificación (art. 14 sexies)."""

    BAJA = "baja"
    MEDIA = "media"
    ALTA = "alta"
    GRAVEDADES = [
        (BAJA, "Baja"),
        (MEDIA, "Media"),
        (ALTA, "Alta"),
    ]

    fecha_deteccion = models.DateTimeField("fecha de detección", default=timezone.now)
    descripcion = models.TextField("descripción")
    datos_afectados = models.TextField("datos afectados", blank=True)
    gravedad = models.CharField("gravedad", max_length=10, choices=GRAVEDADES, default=MEDIA)
    notificado_apdp = models.BooleanField("notificado a la APDP", default=False)
    fecha_notificacion_apdp = models.DateField(
        "fecha de notificación a la APDP", null=True, blank=True
    )
    notificado_titulares = models.BooleanField("notificado a los titulares", default=False)

    class Meta:
        verbose_name = "incidente de seguridad"
        verbose_name_plural = "incidentes de seguridad"
        ordering = ["-fecha_deteccion"]

    def __str__(self):
        return f"Incidente {self.pk} · {self.get_gravedad_display()}"


class RegistroAuditoria(models.Model):
    """Bitácora de escrituras y de accesos a datos personales.

    No lleva borrado lógico: es un registro de solo agregar.
    """

    CREAR = "crear"
    EDITAR = "editar"
    ELIMINAR = "eliminar"
    VER = "ver"
    EXPORTAR = "exportar"
    ACCIONES = [
        (CREAR, "Crear"),
        (EDITAR, "Editar"),
        (ELIMINAR, "Eliminar"),
        (VER, "Ver"),
        (EXPORTAR, "Exportar"),
    ]

    usuario = models.ForeignKey(
        "cuentas.Usuario",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="auditoria",
        verbose_name="usuario",
    )
    accion = models.CharField("acción", max_length=10, choices=ACCIONES)
    tabla = models.CharField("tabla", max_length=80, blank=True)
    objeto_id = models.CharField("objeto", max_length=40, blank=True)
    fecha = models.DateTimeField("fecha", auto_now_add=True)
    ip = models.GenericIPAddressField("IP", null=True, blank=True)
    detalle = models.CharField("detalle", max_length=200, blank=True)

    class Meta:
        verbose_name = "registro de auditoría"
        verbose_name_plural = "registros de auditoría"
        ordering = ["-fecha"]

    def __str__(self):
        return f"{self.get_accion_display()} · {self.tabla} · {self.fecha:%d-%m-%Y %H:%M}"


class Consentimiento(BorradoLogico):
    """Consentimiento del titular, solo cuando el tratamiento se funda en él."""

    vecino = models.ForeignKey(
        "ciudadanos.Vecino",
        on_delete=models.PROTECT,
        related_name="consentimientos",
        verbose_name="titular",
    )
    actividad = models.ForeignKey(
        ActividadTratamiento,
        on_delete=models.PROTECT,
        related_name="consentimientos",
        verbose_name="actividad",
    )
    otorgado = models.BooleanField("otorgado", default=True)
    fecha = models.DateTimeField("fecha", default=timezone.now)
    version_politica = models.CharField("versión de la política", max_length=40, blank=True)
    revocado = models.BooleanField("revocado", default=False)

    class Meta:
        verbose_name = "consentimiento"
        verbose_name_plural = "consentimientos"
        ordering = ["-fecha"]

    def __str__(self):
        return f"{self.vecino} · {self.actividad}"
