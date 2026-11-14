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
            "avance",
            "fecha_compromiso",
            "orden",
        )


class CartaForm(FormularioCRUD):
    campo_delegacion = "delegacion"

    class Meta:
        model = Carta
        fields = (
            "delegacion",
            "asunto",
            "destinatario",
            "fecha",
            "estado",
            "responsable",
            "respuesta",
        )
