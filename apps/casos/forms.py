from apps.casos.models import CasoSocial, Llamada
from apps.common.forms import FormularioCRUD


class CasoSocialForm(FormularioCRUD):
    filas = (
        ("vecino", "responsable"),
        ("fecha_apertura", "estado"),
        ("motivo",),
        ("reingreso", "caso_anterior"),
        ("observaciones",),
    )

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
    filas = (("vecino", "atencion"), ("motivo",), ("fecha_programada", "estado"))

    class Meta:
        model = Llamada
        fields = ("vecino", "atencion", "motivo", "fecha_programada", "estado")
