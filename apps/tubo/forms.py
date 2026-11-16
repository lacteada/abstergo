from apps.common.forms import FormularioCRUD
from apps.tubo.models import Carta, TareaTubo


class TareaTuboForm(FormularioCRUD):
    campo_delegacion = "delegacion"

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


class CartaForm(FormularioCRUD):
    campo_delegacion = "delegacion"

    class Meta:
        model = Carta
        fields = (
            "asunto",
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
