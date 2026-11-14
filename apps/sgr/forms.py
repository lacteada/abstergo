from django import forms
from django.core.exceptions import ValidationError
from django.utils import timezone

from apps.common.forms import FormularioCRUD
from apps.sgr.models import (
    AjusteConducta,
    Alerta,
    Area,
    Ausencia,
    Comentario,
    Evidencia,
    Indicador,
    MetaIndicador,
    Periodo,
    RegistroGestion,
    Validacion,
)


class PeriodoForm(FormularioCRUD):
    class Meta:
        model = Periodo
        fields = (
            "nombre",
            "inicio",
            "termino",
            "dias",
            "situacion",
            "umbral_minimo",
            "umbral_ambar",
            "tope_item",
            "tope_total",
            "estado",
        )


class AreaForm(FormularioCRUD):
    campo_delegacion = "delegacion"

    class Meta:
        model = Area
        fields = ("nombre", "grupo", "cargo", "responsable", "delegacion", "estado")


class IndicadorForm(FormularioCRUD):
    class Meta:
        model = Indicador
        fields = (
            "nombre",
            "grupo",
            "unidad",
            "cargo",
            "tipo_calculo",
            "requiere_evidencia",
            "estado",
        )


class MetaIndicadorForm(FormularioCRUD):
    class Meta:
        model = MetaIndicador
        fields = (
            "periodo",
            "area",
            "indicador",
            "ponderador",
            "meta",
            "funcionario",
            "vigente_desde",
        )


class RegistroGestionForm(FormularioCRUD):
    class Meta:
        model = RegistroGestion
        fields = (
            "fecha",
            "area",
            "indicador",
            "vecino",
            "tipo_atencion",
            "sub_atencion",
            "forma",
            "funcionario",
            "cantidad",
            "detalle",
            "etapa",
            "tipo_solicitante",
            "contacto_nombre",
            "contacto_telefono",
            "accion",
            "actividad",
            "organizacion",
            "estado",
        )

    # Concurrencia optimista (RF-034/RNF-002).
    version = forms.IntegerField(required=False, widget=forms.HiddenInput)

    def __init__(self, *args, request=None, **kwargs):
        super().__init__(*args, request=request, **kwargs)
        if not self.instance.pk:
            self.fields["fecha"].initial = timezone.localdate()
            if request is not None and request.user.is_authenticated:
                self.fields["funcionario"].initial = request.user.pk
        else:
            self.fields["version"].initial = self.instance.version

    def clean(self):
        datos = super().clean()
        if self.instance.pk and datos.get("version") is not None:
            if datos["version"] != self.instance.version:
                raise ValidationError(
                    "Otro usuario modificó este registro; vuelve a abrirlo."
                )
        return datos


class AjusteConductaForm(FormularioCRUD):
    class Meta:
        model = AjusteConducta
        fields = ("area", "tipo", "fecha", "respaldo", "medio", "valor", "periodo")


class AusenciaForm(FormularioCRUD):
    class Meta:
        model = Ausencia
        fields = ("area", "periodo", "tipo", "desde", "hasta", "registrada_por")


class EvidenciaForm(FormularioCRUD):
    class Meta:
        model = Evidencia
        fields = ("registro", "archivo", "vinculo", "tipo")


class ValidacionForm(FormularioCRUD):
    class Meta:
        model = Validacion
        fields = ("evidencia", "decision", "observacion")


class ComentarioForm(FormularioCRUD):
    class Meta:
        model = Comentario
        fields = ("registro", "texto")


class AlertaForm(FormularioCRUD):
    class Meta:
        model = Alerta
        fields = ("tipo", "severidad", "mensaje", "area", "resuelta")
