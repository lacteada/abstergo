from django import forms

from apps.atenciones.models import Atencion
from apps.catalogos.models import SubAtencion, TipoAtencion
from apps.common.estados import ACTIVO
from apps.common.forms import FormularioCRUD


class SelectSubAtencion(forms.Select):
    """Select de sub atenciones que declara su tipo en cada opción.

    El JavaScript lee `data-tipo` para mostrar solo las sub atenciones del tipo
    elegido; el servidor valida lo mismo en `clean`, así que ocultar opciones no
    es la única defensa.
    """

    def create_option(self, name, value, label, selected, index, subindex=None, attrs=None):
        opcion = super().create_option(name, value, label, selected, index, subindex, attrs)
        instancia = getattr(value, "instance", None)
        if instancia is not None:
            opcion["attrs"]["data-tipo"] = instancia.tipo_atencion_id
        return opcion


class AtencionForm(FormularioCRUD):
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
        widgets = {
            "detalle": forms.Textarea(attrs={"rows": 3}),
            "sub_atencion": SelectSubAtencion,
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Los catálogos solo ofrecen lo activo y vigente.
        self.fields["tipo_atencion"].queryset = TipoAtencion.objects.filter(
            estado=ACTIVO
        )
        self.fields["sub_atencion"].queryset = SubAtencion.objects.filter(
            estado=ACTIVO
        )
        if not self.instance.pk:
            self.fields["sub_atencion"].required = False

    def clean(self):
        datos = super().clean()
        tipo = datos.get("tipo_atencion")
        sub = datos.get("sub_atencion")
        if sub and tipo and sub.tipo_atencion_id != tipo.pk:
            self.add_error(
                "sub_atencion",
                "La sub atención elegida no pertenece al tipo seleccionado.",
            )
        return datos
