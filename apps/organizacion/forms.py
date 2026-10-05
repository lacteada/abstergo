from django import forms

from apps.organizacion.models import Delegacion


class DelegacionForm(forms.ModelForm):
    class Meta:
        model = Delegacion
        fields = ("codigo", "nombre", "direccion", "comuna", "responsable")
