"""Base de los formularios del mantenedor.

Todos reciben la petición para acotar los desplegables de delegación a lo que
el perfil tiene autorizado y para precargar la delegación activa al crear. La
restricción se hace sobre el `queryset` del campo, así el servidor rechaza una
delegación no autorizada aunque la petición la altere.
"""

from django import forms
from django.urls import reverse

from apps.common import autocomplete
from apps.common.delegaciones import activa, autorizadas
from apps.common.widgets import (
    CampoFecha,
    CampoFechaHora,
    SelectBuscable,
    SelectMultipleBuscable,
)


def _iso_primero(actuales, iso):
    """Pone los formatos ISO al principio, sin repetir los que ya estaban."""
    return list(iso) + [f for f in actuales if f not in iso]


class FormularioCRUD(forms.ModelForm):
    # Ruta del campo de delegación a acotar ("delegacion" o "territorio").
    campo_delegacion = None
    # Grupos de campos que se dibujan en una misma fila. Cada grupo es una tupla
    # de nombres; el grupo aparece en la posición de su primer campo. Vacío =
    # un campo por fila.
    filas = ()

    def __init__(self, *args, request=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.request = request
        self._acotar_delegacion()
        self._fechas()
        self._buscables()

    def add_error(self, field, error):
        """Marca el campo con error para lectores de pantalla (RNF-010)."""
        super().add_error(field, error)
        if field and field in self.fields:
            widget = self.fields[field].widget
            widget.attrs["aria-invalid"] = "true"
            widget.attrs.setdefault("aria-describedby", f"error_{field}")

    def _fechas(self):
        """Fecha y hora nativas: el navegador ofrece el calendario (RNF-010).

        Solo se tocan los widgets por omisión; un campo con widget propio queda
        como está. El valor va en ISO, que es lo que el navegador espera.
        """
        for campo in self.fields.values():
            if isinstance(campo, forms.DateTimeField) and type(
                campo.widget
            ) is forms.DateTimeInput:
                campo.widget = CampoFechaHora()
                campo.input_formats = _iso_primero(
                    campo.input_formats, ("%Y-%m-%dT%H:%M", "%Y-%m-%dT%H:%M:%S")
                )
            elif isinstance(campo, forms.DateField) and type(
                campo.widget
            ) is forms.DateInput:
                campo.widget = CampoFecha()
                campo.input_formats = _iso_primero(campo.input_formats, ("%Y-%m-%d",))

    @property
    def distribucion(self):
        """Las filas del formulario, como listas de campos, para la plantilla.

        Un grupo se dibuja en la posición de su primer campo presente; los
        campos que la vista quitó (p. ej. `is_active` al crear un usuario) se
        ignoran sin romper la fila.
        """
        nombres = list(self.fields)
        if not self.filas:
            return [[self[nombre]] for nombre in nombres]
        grupos = {}
        for fila in self.filas:
            presentes = [n for n in fila if n in self.fields]
            if presentes:
                grupos[presentes[0]] = presentes
        incluidos = {nombre for grupo in grupos.values() for nombre in grupo}
        filas = []
        for nombre in nombres:
            if nombre in grupos:
                filas.append([self[n] for n in grupos[nombre]])
            elif nombre not in incluidos:
                filas.append([self[nombre]])
        return filas

    def _buscables(self):
        """Pone el buscador en los selects de llave foránea registrados.

        Se aplica una sola vez, acá, así todos los formularios del CRUD lo
        heredan sin declararlo campo por campo. Los widgets propios (p. ej. el
        de Sub Atención) quedan intactos.
        """
        for campo in self.fields.values():
            if isinstance(campo, forms.ModelMultipleChoiceField):
                # M2M: select múltiple con buscador (etiquetas).
                if type(campo.widget) is not forms.SelectMultiple:
                    continue
                slug = autocomplete.slug_de(campo.queryset.model)
                if slug:
                    widget = SelectMultipleBuscable(
                        url=reverse("autocompletar", args=[slug])
                    )
                    widget.choices = campo.choices
                    campo.widget = widget
                continue
            if not isinstance(campo, forms.ModelChoiceField):
                continue
            if type(campo.widget) is not forms.Select:
                continue
            slug = autocomplete.slug_de(campo.queryset.model)
            if slug:
                widget = SelectBuscable(url=reverse("autocompletar", args=[slug]))
                # El widget nuevo hereda las opciones del select que reemplaza.
                widget.choices = campo.choices
                campo.widget = widget

    def _acotar_delegacion(self):
        if not self.campo_delegacion or not self.request:
            return
        campo = self.fields.get(self.campo_delegacion)
        if campo is None:
            return
        campo.queryset = autorizadas(self.request.user)
        if not self.instance.pk:
            actual = activa(self.request)
            if actual is not None and campo.queryset.filter(pk=actual.pk).exists():
                campo.initial = actual.pk
