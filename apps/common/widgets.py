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


class SelectorPersona(forms.Select):
    """Un campo de persona (vecino) con buscador y alta en el mismo formulario.

    El `<select>` queda oculto y `personas.js` dibuja un botón «+» que abre el
    buscador por nombre/RUT. Si la persona no existe, se puede crear escribiendo
    su nombre y RUT: esos dos valores van a los campos ocultos de `crear`
    (por ejemplo `nuevo_presidente_nombre` y `nuevo_presidente_rut`) y el alta
    se guarda junto con el formulario, no al instante. Sin JavaScript queda el
    select completo de siempre.
    """

    def __init__(self, url="", crear=(), etiqueta="", *args, **kwargs):
        self.url = url
        self.crear = ",".join(crear)
        self.etiqueta = etiqueta
        super().__init__(*args, **kwargs)

    def build_attrs(self, base_attrs, extra_attrs=None):
        attrs = super().build_attrs(base_attrs, extra_attrs)
        attrs.update(
            {
                "data-persona-picker": "1",
                "data-url": self.url,
                "data-crear": self.crear,
                "data-etiqueta": self.etiqueta,
            }
        )
        return attrs


class CampoFecha(forms.DateInput):
    """Campo de fecha nativo (`type=date`), con calendario del navegador.

    El valor viaja en ISO (`AAAA-MM-DD`) tanto al pintar como al recibir, así el
    navegador y `flatpickr` (que engancha `input[type=date]`) lo entienden.
    """

    def __init__(self, attrs=None, format="%Y-%m-%d"):
        attrs = {"type": "date", **(attrs or {})}
        super().__init__(attrs=attrs, format=format)


class CampoFechaHora(forms.DateTimeInput):
    """Campo de fecha y hora nativo (`type=datetime-local`)."""

    def __init__(self, attrs=None, format="%Y-%m-%dT%H:%M"):
        attrs = {"type": "datetime-local", **(attrs or {})}
        super().__init__(attrs=attrs, format=format)


class SelectMultipleBuscable(forms.SelectMultiple):
    """Un `<select multiple>` con buscador.

    Agrega `data-multibuscable` y la dirección del motor; `multibuscable.js` lo
    convierte en una caja de etiquetas con búsqueda. Sin JavaScript queda el
    select múltiple de siempre.
    """

    def __init__(self, url="", *args, **kwargs):
        self.url = url
        super().__init__(*args, **kwargs)

    def build_attrs(self, base_attrs, extra_attrs=None):
        attrs = super().build_attrs(base_attrs, extra_attrs)
        if self.url:
            attrs["data-multibuscable"] = "1"
            attrs["data-url"] = self.url
        return attrs


class CampoTelefono(forms.TextInput):
    """Teléfono con teclado numérico en móvil."""

    def __init__(self, attrs=None):
        attrs = {"type": "tel", "inputmode": "tel", **(attrs or {})}
        super().__init__(attrs=attrs)
