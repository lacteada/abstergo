from django import forms

from apps.ciudadanos.models import Vecino


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
