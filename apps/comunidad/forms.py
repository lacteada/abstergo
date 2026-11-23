from django import forms
from django.core.exceptions import ValidationError

from apps.ciudadanos.models import Vecino
from apps.ciudadanos.servicios import crear_vecino, vecinos_autorizados
from apps.common.forms import FormularioCRUD
from apps.comunidad.models import Organizacion

# Los roles de la directiva que son personas (vecinos): se buscan o se crean.
ROLES = ("presidente", "tesorero", "secretario")


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
            "presidente",
            "tesorero",
            "secretario",
            "estado",
        )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Cada rol se resuelve de dos formas: buscar un vecino existente (el
        # select con buscador) o crear la persona aquí mismo. Los campos para
        # crearla van justo debajo de su select, para que el flujo sea continuo.
        for rol in ROLES:
            self.fields[rol].help_text = (
                "Busca el vecino por nombre o RUT, o créalo aquí abajo."
            )
            self.fields[f"nuevo_{rol}_nombre"] = forms.CharField(
                label=f"{rol.capitalize()} nuevo · nombre",
                max_length=120,
                required=False,
                widget=forms.TextInput(attrs={"placeholder": "Nombre y apellido"}),
            )
            self.fields[f"nuevo_{rol}_rut"] = forms.CharField(
                label=f"{rol.capitalize()} nuevo · RUT",
                max_length=15,
                required=False,
                widget=forms.TextInput(attrs={"placeholder": "12345678-9"}),
            )
        self._acotar_directiva()
        self._ordenar()

    def _acotar_directiva(self):
        """Limita los vecinos de la directiva al alcance del usuario."""
        if self.request is None:
            return
        disponibles = vecinos_autorizados(self.request)
        if self.instance.pk:
            # El valor ya elegido debe seguir siendo válido aunque quede fuera
            # del alcance actual (si no, no se podría re-guardar la ficha).
            actuales = filter(
                None,
                (
                    self.instance.presidente_id,
                    self.instance.tesorero_id,
                    self.instance.secretario_id,
                ),
            )
            actuales = list(actuales)
            if actuales:
                disponibles = disponibles | Vecino.objects.filter(pk__in=actuales)
        for rol in ROLES:
            self.fields[rol].queryset = disponibles

    def _ordenar(self):
        """Deja los campos de creación pegados a su select."""
        orden = []
        for nombre in self.fields:
            orden.append(nombre)
            if nombre in ROLES:
                orden += [f"nuevo_{nombre}_nombre", f"nuevo_{nombre}_rut"]
        self.order_fields(orden)

    def clean(self):
        datos = super().clean()
        territorio = datos.get("territorio")
        for rol in ROLES:
            if datos.get(rol):
                continue  # ya se eligió un vecino existente
            nombre = (datos.get(f"nuevo_{rol}_nombre") or "").strip()
            rut = (datos.get(f"nuevo_{rol}_rut") or "").strip()
            if not nombre and not rut:
                continue
            if not (nombre and rut):
                self.add_error(
                    f"nuevo_{rol}_nombre",
                    "Para crear la persona indica nombre y RUT.",
                )
                continue
            if territorio is None:
                self.add_error(
                    "territorio", "Indica el territorio para poder crear personas."
                )
                continue
            try:
                datos[rol] = crear_vecino(nombre, rut, territorio)
            except ValidationError as error:
                self.add_error(f"nuevo_{rol}_rut", error)
        return datos
