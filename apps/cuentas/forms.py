from django import forms
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError

from apps.common.validators import validar_nombre
from apps.cuentas.models import Rol, Usuario


class FormularioLogin(AuthenticationForm):
    """Login por correo.

    Con USERNAME_FIELD apuntando al correo, el campo del formulario sigue
    llamándose `username` por dentro, así que basta con rotularlo.
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


class UsuarioForm(forms.ModelForm):
    """El mantenedor de Usuarios.

    El correo es un dato editable y puede quedar vacío: en ese caso el usuario
    existe pero no puede iniciar sesión. La unicidad la valida el ModelForm,
    porque el campo es único en el modelo.
    """

    nombre = forms.CharField(
        label="Nombre", max_length=150, validators=[validar_nombre]
    )
    apellido = forms.CharField(
        label="Apellido", max_length=150, required=False, validators=[validar_nombre]
    )
    clave = forms.CharField(
        label="Contraseña",
        required=False,
        widget=forms.PasswordInput,
        help_text="En blanco para no cambiarla.",
    )

    class Meta:
        model = Usuario
        fields = ("email", "rol", "delegacion", "is_active")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["email"].required = False
        self.fields["email"].label = "Correo electrónico"
        self.fields["is_active"].label = "Activo"
        if self.instance.pk:
            self.fields["nombre"].initial = self.instance.first_name
            self.fields["apellido"].initial = self.instance.last_name
        else:
            # Al crear hay que definir la contraseña.
            self.fields["clave"].required = True

    def clean_email(self):
        # Dos cadenas vacías chocan contra el índice único; None no.
        return self.cleaned_data.get("email") or None

    def save(self, commit=True):
        usuario = super().save(commit=False)
        usuario.first_name = self.cleaned_data["nombre"]
        usuario.last_name = self.cleaned_data["apellido"]
        clave = self.cleaned_data["clave"]
        if clave:
            usuario.set_password(clave)
        if commit:
            usuario.save()
        return usuario


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
