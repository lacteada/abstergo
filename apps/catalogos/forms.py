from django import forms

from apps.catalogos.models import Meta, SubAtencion, TipoAtencion


class MetaForm(forms.ModelForm):
    class Meta:
        model = Meta
        fields = ("nombre", "descripcion")


class TipoAtencionForm(forms.ModelForm):
    class Meta:
        model = TipoAtencion
        fields = ("nombre", "descripcion")


class SubAtencionForm(forms.ModelForm):
    class Meta:
        model = SubAtencion
        fields = ("nombre", "tipo_atencion")
