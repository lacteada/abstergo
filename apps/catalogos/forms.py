from apps.catalogos.models import Meta, SubAtencion, TipoAtencion
from apps.common.forms import FormularioCRUD


class MetaForm(FormularioCRUD):
    campo_delegacion = "delegacion"

    class Meta:
        model = Meta
        fields = ("codigo", "nombre", "descripcion", "delegacion", "estado")


class TipoAtencionForm(FormularioCRUD):
    class Meta:
        model = TipoAtencion
        fields = ("codigo", "nombre", "descripcion", "estado")


class SubAtencionForm(FormularioCRUD):
    class Meta:
        model = SubAtencion
        fields = ("codigo", "nombre", "tipo_atencion", "estado")
