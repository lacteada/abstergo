from apps.casos.models import CasoSocial
from apps.common.forms import FormularioCRUD


class CasoSocialForm(FormularioCRUD):
    class Meta:
        model = CasoSocial
        fields = (
            "vecino",
            "responsable",
            "fecha_apertura",
            "motivo",
            "estado",
            "reingreso",
            "caso_anterior",
            "observaciones",
        )
