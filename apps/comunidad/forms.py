from apps.common.forms import FormularioCRUD
from apps.comunidad.models import Organizacion


class OrganizacionForm(FormularioCRUD):
    # El `codigo` no se pide: se deriva del nombre (apps/common/codigo.py).
    campo_delegacion = "territorio"

    class Meta:
        model = Organizacion
        fields = (
            "nombre",
            "domicilio_legal",
            "territorio",
            "tipo",
            "subtipo",
            "situacion",
            "verificacion",
            "socios_activos",
            "fecha_constitucion",
            "registro_pj",
            "fecha_inscripcion",
            "registro_dir",
            "estado",
        )
