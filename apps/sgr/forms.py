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
from apps.sgr.validaciones import falta_evidencia


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
            "compromiso",
            "estado",
        )

    # Evidencia adjunta en la misma alta (una por actividad). No son campos del
    # modelo: la vista crea la Evidencia al guardar el registro.
    evidencia_archivo = forms.FileField(
        label="Evidencia (archivo)",
        required=False,
        help_text="JPG, PNG o PDF, hasta 5 MB.",
    )
    evidencia_vinculo = forms.URLField(
        label="Evidencia (vínculo)",
        required=False,
        help_text="Alternativa al archivo: enlace a la evidencia.",
    )
    evidencia_tipo = forms.CharField(
        label="Tipo de evidencia", required=False, max_length=40
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
            # La evidencia se adjunta en el alta; en edición no se toca acá.
            for campo in ("evidencia_archivo", "evidencia_vinculo", "evidencia_tipo"):
                self.fields.pop(campo, None)

    def clean(self):
        datos = super().clean()
        if self.instance.pk and datos.get("version") is not None:
            if datos["version"] != self.instance.version:
                raise ValidationError(
                    "Otro usuario modificó este registro; vuelve a abrirlo."
                )
        if not self.instance.pk:
            self._validar_evidencia(datos)
        return datos

    def _validar_evidencia(self, datos):
        """Exige evidencia cuando el indicador la requiere (RN-010).

        Reutiliza `Evidencia.clean()` para el formato y el tamaño, así la regla
        vive en un solo lugar.
        """
        archivo = datos.get("evidencia_archivo")
        vinculo = datos.get("evidencia_vinculo")
        mensaje = falta_evidencia(datos.get("indicador"), archivo, vinculo)
        if mensaje:
            raise ValidationError({"evidencia_archivo": mensaje})
        if not archivo:
            return
        prueba = Evidencia(archivo=archivo)
        try:
            prueba.clean()
        except ValidationError as error:
            raise ValidationError({"evidencia_archivo": error.messages})


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
