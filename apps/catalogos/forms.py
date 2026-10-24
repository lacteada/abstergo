from apps.catalogos.models import Meta, SubAtencion, TipoAtencion
from apps.common.forms import FormularioCRUD

# En los tres, el `codigo` no se pide: se deriva del nombre
# (apps/common/codigo.py) y lo genera el modelo al guardar.


class MetaForm(FormularioCRUD):
    campo_delegacion = "delegacion"

    class Meta:
        model = Meta
        fields = ("nombre", "descripcion", "delegacion", "estado")


class TipoAtencionForm(FormularioCRUD):
    class Meta:
        model = TipoAtencion
        fields = ("nombre", "descripcion", "estado")


class SubAtencionForm(FormularioCRUD):
    class Meta:
        model = SubAtencion
        fields = ("nombre", "tipo_atencion", "estado")
