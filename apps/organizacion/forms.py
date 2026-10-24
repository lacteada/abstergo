from apps.common.forms import FormularioCRUD
from apps.organizacion.models import Delegacion


class DelegacionForm(FormularioCRUD):
    class Meta:
        # El `codigo` no se pide: se deriva del nombre (apps/common/codigo.py).
        model = Delegacion
        fields = ("nombre", "direccion", "comuna", "responsable", "estado")
