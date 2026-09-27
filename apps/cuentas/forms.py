from django import forms
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError

from apps.cuentas.models import PerfilUsuario, Rol


class FormularioLogin(AuthenticationForm):
    """Login por correo.

    En los datos migrados el correo es el username, así que el formulario
    estándar de Django sirve: solo hay que rotular el campo.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["username"].label = "Correo electrónico"
        self.fields["username"].widget.attrs["placeholder"] = "usuario@muniserena.cl"
        self.fields["password"].label = "Contraseña"


class RolForm(forms.ModelForm):
    class Meta:
        model = Rol
        fields = ("nombre", "descripcion")


class PerfilUsuarioForm(forms.ModelForm):
    """El mantenedor de Usuarios: el perfil y su usuario en un solo formulario."""

    correo = forms.EmailField(label="Correo electrónico")
    nombre = forms.CharField(label="Nombre", max_length=150)
    apellido = forms.CharField(label="Apellido", max_length=150, required=False)
    clave = forms.CharField(
        label="Contraseña",
        required=False,
        widget=forms.PasswordInput,
        help_text="En blanco para no cambiarla.",
    )

    class Meta:
        model = PerfilUsuario
        fields = ("rol", "delegacion", "estado")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance.pk:
            usuario = self.instance.usuario
            self.fields["correo"].initial = usuario.email
            self.fields["nombre"].initial = usuario.first_name
            self.fields["apellido"].initial = usuario.last_name
        else:
            # Al crear hay que definir la contraseña.
            self.fields["clave"].required = True

    def clean_correo(self):
        correo = self.cleaned_data["correo"]
        repetidos = User.objects.filter(username=correo)
        if self.instance.pk:
            repetidos = repetidos.exclude(pk=self.instance.usuario_id)
        if repetidos.exists():
            raise forms.ValidationError("Ya hay un usuario con ese correo.")
        return correo

    def save(self, commit=True):
        perfil = super().save(commit=False)
        datos = self.cleaned_data

        # En un perfil nuevo, perfil.usuario todavía no existe.
        usuario = perfil.usuario if perfil.pk else User()
        usuario.username = datos["correo"]
        usuario.email = datos["correo"]
        usuario.first_name = datos["nombre"]
        usuario.last_name = datos["apellido"]
        if datos["clave"]:
            usuario.set_password(datos["clave"])
        usuario.save()

        if not perfil.pk:
            # El signal post_save ya creó el perfil: se reusa, no se crea otro.
            perfil = PerfilUsuario.objects.get(usuario=usuario)
            perfil.rol = datos["rol"]
            perfil.delegacion = datos["delegacion"]
            perfil.estado = datos["estado"]

        if commit:
            perfil.save()
        return perfil


# --------------------------------------------------- Recuperar la contraseña
class RecuperarForm(forms.Form):
    correo = forms.EmailField(label="Correo electrónico")


class CodigoForm(forms.Form):
    codigo = forms.CharField(
        label="Código de verificación",
        max_length=6,
        min_length=6,
        widget=forms.TextInput(
            attrs={"class": "codigo", "inputmode": "numeric", "autocomplete": "off"}
        ),
    )

    def clean_codigo(self):
        codigo = self.cleaned_data["codigo"].strip()
        if not codigo.isdigit():
            raise forms.ValidationError("El código son 6 dígitos.")
        return codigo


class NuevaPasswordForm(forms.Form):
    password1 = forms.CharField(
        label="Nueva contraseña", widget=forms.PasswordInput
    )
    password2 = forms.CharField(
        label="Confirmar nueva contraseña", widget=forms.PasswordInput
    )

    def clean(self):
        datos = super().clean()
        password1 = datos.get("password1")
        if password1 and password1 != datos.get("password2"):
            raise forms.ValidationError("Las contraseñas no coinciden.")
        if password1:
            try:
                validate_password(password1)
            except ValidationError as error:
                raise forms.ValidationError(error.messages) from error
        return datos
