from apps.common.forms import FormularioCRUD
from apps.organizacion.models import Cargo, Delegacion, Territorio


class DelegacionForm(FormularioCRUD):
    class Meta:
        # El `codigo` no se pide: se deriva del nombre (apps/common/codigo.py).
        model = Delegacion
        fields = ("nombre", "direccion", "comuna", "responsable", "estado")


class CargoForm(FormularioCRUD):
    class Meta:
        # El `codigo` no se pide: se deriva del nombre (apps/common/codigo.py).
        model = Cargo
        fields = ("nombre", "descripcion", "funciones")


class TerritorioForm(FormularioCRUD):
    class Meta:
        model = Territorio
        fields = ("nombre", "delegacion", "estado")
