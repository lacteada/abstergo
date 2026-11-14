from apps.common.forms import FormularioCRUD
from apps.tubo.models import TareaTubo


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
