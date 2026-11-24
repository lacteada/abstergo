from django import forms
from django.core.exceptions import ValidationError
from django.urls import reverse

from apps.ciudadanos.models import Vecino
from apps.ciudadanos.servicios import crear_vecino, vecinos_autorizados
from apps.common.forms import FormularioCRUD
from apps.common.widgets import SelectorPersona
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
        # La directiva son tres personas. Cada cargo es un buscador (personas.js
        # dibuja el botón «+» sobre el select) y, si la persona no existe, se
        # crea con los campos ocultos: el alta se guarda junto con el formulario.
        url_vecino = reverse("autocompletar", args=["vecino"])
        for rol in ROLES:
            self.fields[f"nuevo_{rol}_nombre"] = forms.CharField(
                max_length=120, required=False, widget=forms.HiddenInput()
            )
            self.fields[f"nuevo_{rol}_rut"] = forms.CharField(
                max_length=15, required=False, widget=forms.HiddenInput()
            )
            widget = SelectorPersona(
                url=url_vecino,
                crear=(f"nuevo_{rol}_nombre", f"nuevo_{rol}_rut"),
                etiqueta=rol.capitalize(),
            )
            # El widget nuevo hereda las opciones del select que reemplaza.
            widget.choices = self.fields[rol].choices
            self.fields[rol].widget = widget
            self.fields[rol].help_text = ""
        # Distribución en filas: los tres cargos de la directiva van juntos.
        self.filas = (
            ("domicilio_legal", "territorio"),
            ("tipo", "subtipo"),
            ("situacion", "verificacion"),
            ("socios_activos", "registro_pj"),
            ("fecha_constitucion", "fecha_inscripcion"),
            (
                "presidente",
                "tesorero",
                "secretario",
                "nuevo_presidente_nombre",
                "nuevo_presidente_rut",
                "nuevo_tesorero_nombre",
                "nuevo_tesorero_rut",
                "nuevo_secretario_nombre",
                "nuevo_secretario_rut",
            ),
        )
        self._acotar_directiva()

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
