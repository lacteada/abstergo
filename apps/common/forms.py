"""Base de los formularios del mantenedor.

Todos reciben la petición para acotar los desplegables de delegación a lo que
el perfil tiene autorizado y para precargar la delegación activa al crear. La
restricción se hace sobre el `queryset` del campo, así el servidor rechaza una
delegación no autorizada aunque la petición la altere.
"""

from django import forms

from apps.common.delegaciones import activa, autorizadas


class FormularioCRUD(forms.ModelForm):
    # Ruta del campo de delegación a acotar ("delegacion" o "territorio").
    campo_delegacion = None

    def __init__(self, *args, request=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.request = request
        self._acotar_delegacion()

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
