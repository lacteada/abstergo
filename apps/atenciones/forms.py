from django import forms

from apps.atenciones.models import Atencion


class AtencionForm(forms.ModelForm):
    class Meta:
        model = Atencion
        fields = (
            "tipo_atencion",
            "sub_atencion",
            "motivo",
            "detalle",
            "estado",
            "canal",
        )
        widgets = {"detalle": forms.Textarea(attrs={"rows": 3})}
