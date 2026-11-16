from apps.casos.models import CasoSocial, Llamada
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


class LlamadaForm(FormularioCRUD):
    class Meta:
        model = Llamada
        fields = ("vecino", "atencion", "motivo", "fecha_programada", "estado")
