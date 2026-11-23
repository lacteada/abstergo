"""Modelos de la Matriz SGR (Sistema de Gestión de Resultados).

Reproduce la planilla de las Delegaciones: por trimestre, cada área (cargo o
puesto) tiene indicadores con su ponderador y su meta; las gestiones diarias se
registran y los reclamos/felicitaciones y los días de ausencia ajustan el
resultado. El puntaje se calcula en `apps/sgr/calculos.py`.
"""

from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone

from apps.common.codigo import ConCodigoDerivado
from apps.common.estados import ConEstado
from apps.common.referencia import ConReferencia
from apps.common.soft_delete import BorradoLogico
from apps.common.validators import (
    validar_catalogo,
    validar_codigo,
    validar_telefono,
    validar_texto,
)

# Grupos de la matriz (las "áreas" de la consolidación del documento).
GRUPOS = [
    ("apoyo-administrativo", "Apoyo administrativo"),
    ("territorial-oocc", "Territorial OO.CC."),
    ("coordinador-servicios", "Coordinador de servicios comunitarios"),
    ("gestor-social", "Gestor social"),
    ("planificacion-control", "Planificación y control"),
    ("seguridad", "Seguridad ciudadana"),
]

UNIDADES = [
    ("gestiones", "Gestiones"),
    ("porcentaje", "Porcentaje"),
]

CONDUCTAS = [
    ("reclamo", "Reclamo"),
    ("felicitacion", "Felicitación"),
]

MEDIOS = [
    ("oficio", "Oficio"),
    ("correo", "Correo"),
    ("presencial", "Presencial"),
    ("otro", "Otro"),
]

ACTIVIDADES = [
    ("visita", "Visita"),
    ("reunion", "Reunión"),
    ("taller", "Taller"),
    ("conformacion", "Conformación"),
    ("otra", "Otra"),
]

AUSENCIAS = [
    ("licencia", "Licencia"),
    ("vacaciones", "Vacaciones"),
    ("emergencia", "Emergencia"),
    ("compensatorio", "Compensatorio administrativo"),
]

# Situación del período (distinta de la vigencia activo/inactivo).
SITUACIONES = [
    ("abierto", "Abierto"),
    ("cerrado", "Cerrado"),
    ("reabierto", "Reabierto"),
]

TIPOS_CALCULO = [
    ("conteo", "Conteo"),
    ("razon", "Razón / porcentaje"),
    ("documento", "Documento"),
    ("automatico", "Automático"),
]

ETAPAS = [
    ("preparatoria", "Preparatoria"),
    ("ejecutada", "Ejecutada"),
]

SOLICITANTES = [
    ("externo", "Externo"),
    ("delegado", "Delegado"),
]

ESTADOS_REGISTRO = [
    ("registrada", "Registrada"),
    ("pendiente_validacion", "Pendiente de validación"),
    ("aprobada", "Aprobada"),
    ("rechazada", "Rechazada"),
    ("correccion", "Corrección solicitada"),
    ("anulada", "Anulada"),
]

# Estados del registro que sí suman al avance (RF-014, RN-010).
ESTADOS_VALIDOS = ("registrada", "aprobada")


class Periodo(ConReferencia, ConCodigoDerivado, ConEstado, BorradoLogico):
    """Un trimestre de evaluación."""

    PREFIJO = "PER"

    codigo = models.CharField(
        "código", max_length=40, unique=True, validators=[validar_codigo]
    )
    nombre = models.CharField(
        "nombre", max_length=120, unique=True, validators=[validar_catalogo]
    )
    inicio = models.DateField("inicio")
    termino = models.DateField("término")
    dias = models.PositiveIntegerField("días", null=True, blank=True)
    situacion = models.CharField(
        "situación", max_length=10, choices=SITUACIONES, default="abierto"
    )
    umbral_minimo = models.DecimalField(
        "umbral mínimo", max_digits=4, decimal_places=2, default=Decimal("0.80")
    )
    umbral_ambar = models.DecimalField(
        "umbral ámbar", max_digits=4, decimal_places=2, default=Decimal("0.60")
    )
    tope_item = models.DecimalField(
        "tope por ítem", max_digits=4, decimal_places=2, default=Decimal("1.20")
    )
    tope_total = models.DecimalField(
        "tope total", max_digits=4, decimal_places=2, default=Decimal("1.50")
    )
    version = models.PositiveIntegerField("versión", default=1)
    reabierto_por = models.ForeignKey(
        "cuentas.Usuario",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="periodos_reabiertos",
        verbose_name="reabierto por",
    )
    reabierto_motivo = models.CharField(
        "motivo de reapertura", max_length=200, blank=True
    )

    class Meta:
        verbose_name = "período"
        verbose_name_plural = "períodos"
        ordering = ["-inicio"]

    def __str__(self):
        return self.nombre

    @property
    def dias_totales(self):
        """Los días del trimestre: el dato explícito o los del rango."""
        if self.dias:
            return self.dias
        return (self.termino - self.inicio).days + 1

    def fraccion_transcurrida(self, hoy=None):
        """Qué parte del período ha pasado (0 a 1), para la meta al día."""
        hoy = hoy or timezone.localdate()
        total = self.dias_totales
        if total <= 0 or hoy <= self.inicio:
            return 0.0
        transcurridos = (min(hoy, self.termino) - self.inicio).days + 1
        return max(0.0, min(1.0, transcurridos / total))

    def dias_transcurridos(self, hoy=None):
        """Días corridos desde el inicio hasta hoy (sin pasar del término)."""
        hoy = hoy or timezone.localdate()
        if hoy <= self.inicio:
            return 0
        return (min(hoy, self.termino) - self.inicio).days + 1

    def esta_cerrado(self):
        """Un período cerrado no admite cambios sin reapertura (RN-013)."""
        return self.situacion == "cerrado"

    def clean(self):
        if self.inicio and self.termino and self.termino < self.inicio:
            raise ValidationError(
                {"termino": "El término no puede ser anterior al inicio."}
            )


class Area(ConReferencia, ConCodigoDerivado, ConEstado, BorradoLogico):
    """Un puesto de la matriz: el cargo, su responsable y su territorio."""

    PREFIJO = "ARE"

    codigo = models.CharField(
        "código", max_length=40, unique=True, validators=[validar_codigo]
    )
    nombre = models.CharField(
        "nombre", max_length=120, validators=[validar_catalogo]
    )
    grupo = models.CharField("grupo", max_length=40, choices=GRUPOS)
    cargo = models.ForeignKey(
        "organizacion.Cargo",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="areas_sgr",
        verbose_name="cargo",
    )
    responsable = models.ForeignKey(
        "cuentas.Usuario",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="areas_sgr",
        verbose_name="responsable",
    )
    delegacion = models.ForeignKey(
        "organizacion.Delegacion",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="areas_sgr",
        verbose_name="delegación",
    )
    excepcion_ponderadores = models.BooleanField(
        "excepción de ponderadores", default=False
    )

    class Meta:
        verbose_name = "área"
        verbose_name_plural = "áreas"
        ordering = ["grupo", "nombre"]

    def __str__(self):
        return self.nombre


class Indicador(ConReferencia, ConCodigoDerivado, ConEstado, BorradoLogico):
    """Un ítem de la matriz: lo que se cuenta y se pondera."""

    PREFIJO = "IND"

    codigo = models.CharField(
        "código", max_length=40, unique=True, validators=[validar_codigo]
    )
    nombre = models.CharField("nombre", max_length=200, validators=[validar_texto])
    grupo = models.CharField("grupo", max_length=40, choices=GRUPOS)
    unidad = models.CharField(
        "unidad", max_length=12, choices=UNIDADES, default="gestiones"
    )
    cargo = models.ForeignKey(
        "organizacion.Cargo",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="indicadores_sgr",
        verbose_name="cargo",
    )
    tipo_calculo = models.CharField(
        "tipo de cálculo", max_length=12, choices=TIPOS_CALCULO, default="conteo"
    )
    requiere_evidencia = models.BooleanField("requiere evidencia", default=False)

    class Meta:
        verbose_name = "indicador"
        verbose_name_plural = "indicadores"
        ordering = ["grupo", "nombre"]

    def __str__(self):
        return self.nombre


class MetaIndicador(ConReferencia, BorradoLogico):
    """Cuánto pesa y cuánto se espera de un indicador, en un área y período."""

    PREFIJO = "MIN"

    periodo = models.ForeignKey(
        Periodo, on_delete=models.PROTECT, related_name="metas", verbose_name="período"
    )
    area = models.ForeignKey(
        Area, on_delete=models.PROTECT, related_name="metas", verbose_name="área"
    )
    indicador = models.ForeignKey(
        Indicador,
        on_delete=models.PROTECT,
        related_name="metas",
        verbose_name="indicador",
    )
    ponderador = models.DecimalField(
        "ponderador", max_digits=6, decimal_places=3, default=0
    )
    meta = models.DecimalField("meta", max_digits=10, decimal_places=2, default=0)
    funcionario = models.ForeignKey(
        "cuentas.Usuario",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="metas_sgr",
        verbose_name="funcionario",
    )
    vigente_desde = models.DateField("vigente desde", null=True, blank=True)

    class Meta:
        verbose_name = "meta de indicador"
        verbose_name_plural = "metas de indicador"
        ordering = ["periodo", "area", "indicador"]
        constraints = [
            models.UniqueConstraint(
                fields=["periodo", "area", "indicador"], name="meta_por_area_indicador"
            )
        ]

    def __str__(self):
        return f"{self.area} · {self.indicador}"

    def clean(self):
        # RN-002: un ítem cuantitativo exige meta mayor que cero.
        if (
            self.indicador_id
            and self.indicador.unidad == "gestiones"
            and (self.meta is None or self.meta <= 0)
        ):
            raise ValidationError(
                {"meta": "La meta de un ítem cuantitativo debe ser mayor que cero."}
            )


class RegistroGestion(ConReferencia, BorradoLogico):
    """Una gestión diaria de la matriz (el registro que da puntaje)."""

    PREFIJO = "GES"

    fecha = models.DateField("fecha", default=timezone.localdate)
    area = models.ForeignKey(
        Area, on_delete=models.PROTECT, related_name="registros", verbose_name="área"
    )
    indicador = models.ForeignKey(
        Indicador,
        on_delete=models.PROTECT,
        related_name="registros",
        verbose_name="indicador",
    )
    vecino = models.ForeignKey(
        "ciudadanos.Vecino",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="registros_sgr",
        verbose_name="vecino",
    )
    funcionario = models.ForeignKey(
        "cuentas.Usuario",
        on_delete=models.PROTECT,
        related_name="registros_sgr",
        verbose_name="funcionario",
    )
    cantidad = models.PositiveIntegerField("cantidad", default=1)
    detalle = models.TextField("detalle", blank=True)
    etapa = models.CharField(
        "etapa", max_length=12, choices=ETAPAS, default="ejecutada"
    )
    tipo_solicitante = models.CharField(
        "tipo de solicitante", max_length=10, choices=SOLICITANTES, default="externo"
    )
    contacto_nombre = models.CharField("contacto (nombre)", max_length=120, blank=True)
    contacto_telefono = models.CharField(
        "contacto (teléfono)", max_length=30, blank=True, validators=[validar_telefono]
    )
    puntua = models.BooleanField("puntúa", default=True)
    motivo_no_puntua = models.CharField("motivo sin puntaje", max_length=120, blank=True)
    estado = models.CharField(
        "estado", max_length=20, choices=ESTADOS_REGISTRO, default="registrada"
    )
    accion = models.CharField("acción", max_length=200, blank=True)
    actividad = models.CharField(
        "actividad", max_length=14, choices=ACTIVIDADES, blank=True
    )
    organizacion = models.ForeignKey(
        "comunidad.Organizacion",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="registros_sgr",
        verbose_name="organización",
    )
    compromiso = models.ForeignKey(
        "tubo.TareaTubo",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="actividades",
        verbose_name="compromiso",
    )
    # Concurrencia optimista (RF-034/RNF-002): cambia en cada guardado.
    version = models.PositiveIntegerField("versión", default=1)

    class Meta:
        verbose_name = "actividad"
        verbose_name_plural = "actividades"
        ordering = ["-fecha", "-pk"]

    def __str__(self):
        return f"{self.referencia} · {self.indicador} · {self.fecha:%d-%m-%Y}"

    def save(self, *args, **kwargs):
        from apps.sgr.validaciones import evaluar_puntaje

        self.puntua, self.motivo_no_puntua = evaluar_puntaje(
            self.etapa,
            self.tipo_solicitante,
            self.contacto_nombre,
            self.contacto_telefono,
        )
        if not kwargs.get("update_fields"):
            self.version = (self.version or 0) + 1
        super().save(*args, **kwargs)

    def clean(self):
        # Reglas del requerimiento del 4° trimestre (doc 1).
        from apps.sgr.validaciones import MAX_REGISTROS_DIA, en_semana_actual

        if self.fecha and not en_semana_actual(self.fecha, timezone.localdate()):
            raise ValidationError(
                {"fecha": "Solo se registran gestiones de la semana en curso."}
            )
        if self.fecha:
            periodo = Periodo.objects.filter(
                inicio__lte=self.fecha, termino__gte=self.fecha
            ).first()
            if periodo and periodo.esta_cerrado():
                raise ValidationError(
                    {"fecha": "El período está cerrado y no admite cambios."}
                )
        if self.funcionario_id and self.fecha:
            mismo_dia = type(self).objects.filter(
                funcionario_id=self.funcionario_id, fecha=self.fecha
            )
            if self.pk:
                mismo_dia = mismo_dia.exclude(pk=self.pk)
            if mismo_dia.count() + 1 > MAX_REGISTROS_DIA:
                raise ValidationError(
                    {"fecha": f"Máximo {MAX_REGISTROS_DIA} registros por día."}
                )


class AjusteConducta(ConReferencia, BorradoLogico):
    """Un reclamo o una felicitación que ajusta el puntaje de un área."""

    PREFIJO = "AJU"

    area = models.ForeignKey(
        Area, on_delete=models.PROTECT, related_name="conductas", verbose_name="área"
    )
    tipo = models.CharField("tipo", max_length=12, choices=CONDUCTAS)
    fecha = models.DateField("fecha", default=timezone.localdate)
    respaldo = models.CharField(
        "respaldo", max_length=200, blank=True, validators=[validar_texto]
    )
    medio = models.CharField("medio", max_length=12, choices=MEDIOS, blank=True)
    valor = models.DecimalField(
        "valor", max_digits=4, decimal_places=2, null=True, blank=True
    )
    periodo = models.ForeignKey(
        Periodo,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="conductas",
        verbose_name="período",
    )

    class Meta:
        verbose_name = "reclamo o felicitación"
        verbose_name_plural = "reclamos y felicitaciones"
        ordering = ["-fecha"]

    def __str__(self):
        return f"{self.get_tipo_display()} · {self.area}"

    def save(self, *args, **kwargs):
        from apps.sgr.validaciones import valor_conducta

        if self.valor is None:
            cargo = self.area.cargo.codigo if self.area_id and self.area.cargo_id else None
            self.valor = valor_conducta(self.tipo, cargo)
        super().save(*args, **kwargs)

    def clean(self):
        # Una felicitación solo vale si la informa el delegado con respaldo (doc 1).
        if self.tipo == "felicitacion" and not self.respaldo:
            raise ValidationError({"respaldo": "Una felicitación requiere respaldo."})


class Ausencia(ConReferencia, BorradoLogico):
    """Ausencia de un área/funcionario que ajusta la meta al día (doc 1, semáforo)."""

    PREFIJO = "AUS"

    area = models.ForeignKey(
        Area, on_delete=models.PROTECT, related_name="ausencias", verbose_name="área"
    )
    periodo = models.ForeignKey(
        Periodo,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="ausencias",
        verbose_name="período",
    )
    tipo = models.CharField("tipo", max_length=14, choices=AUSENCIAS)
    desde = models.DateField("desde")
    hasta = models.DateField("hasta")
    registrada_por = models.ForeignKey(
        "cuentas.Usuario",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="ausencias_sgr",
        verbose_name="registrada por",
    )

    class Meta:
        verbose_name = "ausencia"
        verbose_name_plural = "ausencias"
        ordering = ["area", "-desde"]

    def __str__(self):
        return f"{self.area} · {self.get_tipo_display()} ({self.desde} a {self.hasta})"

    @property
    def dias(self):
        if not (self.desde and self.hasta):
            return 0
        return max(0, (self.hasta - self.desde).days + 1)


class Evidencia(ConReferencia, BorradoLogico):
    """Respaldo de una gestión (foto o vínculo) con su estado de revisión."""

    PREFIJO = "EVE"

    REVISIONES = [
        ("pendiente", "Pendiente"),
        ("aprobada", "Aprobada"),
        ("rechazada", "Rechazada"),
        ("correccion", "Corrección solicitada"),
    ]

    EXTENSIONES = ("jpg", "jpeg", "png", "pdf")
    TAMANO_MAX = 5 * 1024 * 1024

    registro = models.ForeignKey(
        RegistroGestion,
        on_delete=models.PROTECT,
        related_name="evidencias",
        verbose_name="registro",
    )
    archivo = models.FileField("archivo", upload_to="evidencias/", null=True)
    vinculo = models.URLField("vínculo", max_length=300, blank=True)
    autor = models.ForeignKey(
        "cuentas.Usuario",
        on_delete=models.PROTECT,
        related_name="evidencias_sgr",
        verbose_name="autor",
    )
    fecha = models.DateTimeField("fecha", default=timezone.now)
    tipo = models.CharField("tipo", max_length=40, blank=True)
    tamano = models.PositiveIntegerField("tamaño", null=True, blank=True)
    huella = models.CharField("huella", max_length=64, blank=True)
    estado_revision = models.CharField(
        "estado de revisión", max_length=12, choices=REVISIONES, default="pendiente"
    )

    class Meta:
        verbose_name = "evidencia"
        verbose_name_plural = "evidencias"
        ordering = ["-fecha"]

    def __str__(self):
        return f"{self.referencia} · {self.registro}"

    def clean(self):
        # Una evidencia vale con archivo o con vínculo; el archivo, si viene,
        # pasa por formato y tamaño (RNF-009).
        if not (self.archivo or self.vinculo):
            raise ValidationError(
                {"archivo": "La evidencia debe incluir un archivo o un vínculo."}
            )
        if not self.archivo:
            return
        nombre = getattr(self.archivo, "name", "") or ""
        extension = nombre.rsplit(".", 1)[-1].lower() if "." in nombre else ""
        if extension not in self.EXTENSIONES:
            raise ValidationError(
                {"archivo": "Formato no permitido (usa jpg, png o pdf)."}
            )
        try:
            tamano = self.archivo.size
        except (OSError, ValueError):
            tamano = 0
        if tamano > self.TAMANO_MAX:
            raise ValidationError({"archivo": "El archivo supera el máximo de 5 MB."})


class Validacion(ConReferencia, BorradoLogico):
    """Revisión de una evidencia por un verificador (quien registra no valida)."""

    PREFIJO = "VAL"

    DECISIONES = [
        ("aprobada", "Aprobada"),
        ("rechazada", "Rechazada"),
        ("correccion", "Corrección solicitada"),
    ]

    evidencia = models.ForeignKey(
        Evidencia,
        on_delete=models.PROTECT,
        related_name="validaciones",
        verbose_name="evidencia",
    )
    verificador = models.ForeignKey(
        "cuentas.Usuario",
        on_delete=models.PROTECT,
        related_name="validaciones_sgr",
        verbose_name="verificador",
    )
    decision = models.CharField("decisión", max_length=12, choices=DECISIONES)
    fecha = models.DateTimeField("fecha", default=timezone.now)
    observacion = models.TextField("observación", blank=True)
    version = models.PositiveIntegerField("versión", default=1)

    class Meta:
        verbose_name = "validación"
        verbose_name_plural = "validaciones"
        ordering = ["-fecha"]

    def __str__(self):
        return f"{self.get_decision_display()} · {self.evidencia}"

    def clean(self):
        # RNF-004: segregación de funciones.
        if (
            self.evidencia_id
            and self.verificador_id
            and self.evidencia.registro.funcionario_id == self.verificador_id
        ):
            raise ValidationError(
                {"verificador": "Quien registra no puede validar su propia evidencia."}
            )

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        evidencia = self.evidencia
        evidencia.estado_revision = self.decision
        evidencia.save(update_fields=["estado_revision"])
        registro = evidencia.registro
        if self.decision == "aprobada":
            registro.estado = "aprobada"
        elif self.decision == "correccion":
            registro.estado = "correccion"
        else:
            registro.estado = "rechazada"
        registro.save(update_fields=["estado"])
        # Al aprobar la evidencia, el compromiso de origen queda realizado (RF-020).
        if self.decision == "aprobada" and registro.compromiso_id:
            registro.compromiso.estado = "realizada"
            registro.compromiso.save(update_fields=["estado"])


class Comentario(ConReferencia, BorradoLogico):
    """Un comentario sobre un registro de gestión (RF-035)."""

    PREFIJO = "COM"

    registro = models.ForeignKey(
        RegistroGestion,
        on_delete=models.PROTECT,
        related_name="comentarios",
        verbose_name="registro",
    )
    autor = models.ForeignKey(
        "cuentas.Usuario",
        on_delete=models.PROTECT,
        related_name="comentarios_sgr",
        verbose_name="autor",
    )
    texto = models.TextField("texto")
    fecha = models.DateTimeField("fecha", default=timezone.now)

    class Meta:
        verbose_name = "comentario"
        verbose_name_plural = "comentarios"
        ordering = ["-fecha"]

    def __str__(self):
        return f"{self.autor} · {self.texto[:40]}"


class Alerta(ConReferencia, BorradoLogico):
    """Una alerta del sistema (RF-037)."""

    PREFIJO = "ALE"

    TIPOS = [
        ("tarea-vencida", "Tarea vencida"),
        ("item-bajo-umbral", "Ítem bajo umbral"),
        ("reclamo-repetido", "Reclamos repetidos"),
        ("periodo-por-cerrar", "Período por cerrar"),
        ("ingreso-sospechoso", "Ingreso sospechoso"),
        ("organizacion-sin-visita", "Organización sin visita"),
    ]

    SEVERIDADES = [("alta", "Alta"), ("media", "Media"), ("baja", "Baja")]

    tipo = models.CharField("tipo", max_length=30, choices=TIPOS)
    severidad = models.CharField(
        "severidad", max_length=6, choices=SEVERIDADES, default="media"
    )
    mensaje = models.CharField("mensaje", max_length=200, validators=[validar_texto])
    area = models.ForeignKey(
        Area,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="alertas",
        verbose_name="área",
    )
    resuelta = models.BooleanField("resuelta", default=False)
    fecha = models.DateTimeField("fecha", default=timezone.now)

    class Meta:
        verbose_name = "alerta"
        verbose_name_plural = "alertas"
        ordering = ["resuelta", "-fecha"]

    def __str__(self):
        return f"{self.get_tipo_display()} · {self.mensaje[:40]}"
