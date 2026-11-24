from apps.ciudadanos.models import Vecino
from apps.common.forms import FormularioCRUD
from apps.common.validators import normalizar_rut
from apps.common.widgets import CampoTelefono


class VecinoForm(FormularioCRUD):
    campo_delegacion = "territorio"
    filas = (
        ("nombre", "rut"),
        ("telefono", "territorio"),
        ("direccion",),
        ("tipo_gestion", "estado"),
    )

    class Meta:
        model = Vecino
        fields = (
            "nombre",
            "rut",
            "direccion",
            "telefono",
            "territorio",
            "tipo_gestion",
            "estado",
        )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Ayudas de entrada: el RUT se escribe tal cual; el teléfono abre teclado.
        self.fields["rut"].widget.attrs.update(
            {
                "placeholder": "12345678-9",
                "autocomplete": "off",
                "maxlength": "15",
                "autocapitalize": "characters",
            }
        )
        self.fields["telefono"].widget = CampoTelefono(
            attrs={"placeholder": "+56 9 1234 5678"}
        )

    def clean_rut(self):
        # Guarda el RUT en la forma canónica 12345678-9.
        return normalizar_rut(self.cleaned_data["rut"])
