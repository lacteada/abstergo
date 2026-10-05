from django import forms

from apps.ciudadanos.models import Vecino
from apps.common.validators import normalizar_rut


class VecinoForm(forms.ModelForm):
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

    def clean_rut(self):
        # Guarda el RUT en la forma canónica 12345678-9.
        return normalizar_rut(self.cleaned_data["rut"])
