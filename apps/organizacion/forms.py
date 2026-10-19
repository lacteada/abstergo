from apps.common.forms import FormularioCRUD
from apps.organizacion.models import Delegacion


class DelegacionForm(FormularioCRUD):
    class Meta:
        model = Delegacion
        fields = ("codigo", "nombre", "direccion", "comuna", "responsable", "estado")
