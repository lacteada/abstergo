from apps.casos.models import CasoSocial, GestionCaso, Llamada
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


class GestionCasoForm(FormularioCRUD):
    class Meta:
        model = GestionCaso
        fields = ("caso", "fecha", "tipo", "hito", "plazo", "detalle")


class LlamadaForm(FormularioCRUD):
    class Meta:
        model = Llamada
        fields = ("vecino", "motivo", "fecha_programada", "estado", "responsable", "resultado")
