from apps.common.forms import FormularioCRUD
from apps.organizacion.models import Cargo, Delegacion, Territorio


class DelegacionForm(FormularioCRUD):
    filas = (("nombre",), ("direccion", "comuna"), ("responsable", "estado"))

    class Meta:
        # El `codigo` no se pide: se deriva del nombre (apps/common/codigo.py).
        model = Delegacion
        fields = ("nombre", "direccion", "comuna", "responsable", "estado")


class CargoForm(FormularioCRUD):
    filas = (("nombre", "descripcion"), ("funciones",))

    class Meta:
        # El `codigo` no se pide: se deriva del nombre (apps/common/codigo.py).
        model = Cargo
        fields = ("nombre", "descripcion", "funciones")


class TerritorioForm(FormularioCRUD):
    filas = (("nombre", "delegacion"), ("estado",))

    class Meta:
        model = Territorio
        fields = ("nombre", "delegacion", "estado")
