from django import forms

from apps.common.forms import FormularioCRUD
from apps.tubo.models import Carta, TareaTubo


class TareaTuboForm(FormularioCRUD):
    campo_delegacion = "delegacion"
    filas = (
        ("titulo", "tipo"),
        ("descripcion",),
        ("delegacion", "territorio"),
        ("responsable", "apoyo"),
        ("solicitante", "vecino"),
        ("atencion",),
        ("fecha_compromiso", "avance"),
        ("estado",),
    )

    class Meta:
        model = TareaTubo
        fields = (
            "titulo",
            "descripcion",
            "estado",
            "delegacion",
            "territorio",
            "tipo",
            "solicitante",
            "responsable",
            "apoyo",
            "vecino",
            "atencion",
            "avance",
            "fecha_compromiso",
            "orden",
        )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # El orden lo administra el tablero (kanban), no la persona.
        self.fields["orden"].widget = forms.HiddenInput()


class CartaForm(FormularioCRUD):
    campo_delegacion = "delegacion"
    filas = (
        ("asunto", "tipo"),
        ("correlativo", "destinatario"),
        ("remitente", "contacto"),
        ("fecha", "encargado"),
        ("delegacion", "estado"),
        ("observacion",),
    )

    class Meta:
        model = Carta
        fields = (
            "asunto",
            "tipo",
            "correlativo",
            "destinatario",
            "remitente",
            "contacto",
            "fecha",
            "encargado",
            "delegacion",
            "estado",
            "observacion",
        )
