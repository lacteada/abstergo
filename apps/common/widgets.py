"""Widgets compartidos por los formularios del CRUD."""

from django import forms


class SelectBuscable(forms.Select):
    """Un `<select>` con buscador.

    Agrega `data-autocomplete` con la dirección del motor; `autocomplete.js` lo
    convierte en un combobox. Sin JavaScript queda el select completo de
    siempre, así que no se pierde nada.
    """

    def __init__(self, url="", *args, **kwargs):
        self.url = url
        super().__init__(*args, **kwargs)

    def build_attrs(self, base_attrs, extra_attrs=None):
        attrs = super().build_attrs(base_attrs, extra_attrs)
        if self.url:
            attrs["data-autocomplete"] = self.url
        return attrs
