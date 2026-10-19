from django import forms
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator

from apps.common.forms import FormularioCRUD
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


class RolForm(FormularioCRUD):
    class Meta:
        model = Rol
        fields = ("codigo", "nombre", "descripcion")


class UsuarioForm(FormularioCRUD):
    """El mantenedor de Usuarios.

    El administrador no define la contraseña: al crear la cuenta nace
    **pendiente** (sin contraseña usable y sin acceso) y se le envía un correo
    para activarla y fijar su clave. Por eso el correo es obligatorio al crear:
    es el único camino de activación. `delegaciones_autorizadas` es la lista
    que el selector de contexto puede ofrecer.
    """

    nombre = forms.CharField(
        label="Nombre", max_length=150, validators=[validar_nombre]
    )
    apellido = forms.CharField(
        label="Apellido", max_length=150, required=False, validators=[validar_nombre]
    )

    class Meta:
        model = Usuario
        fields = (
            "email",
            "rol",
            "delegacion",
            "delegaciones_autorizadas",
            "is_active",
        )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.creando = self.instance.pk is None
        self.fields["email"].label = "Correo electrónico"
        self.fields["is_active"].label = "Activo"
        if self.creando:
            self.fields["email"].required = True
            self.fields["email"].help_text = (
                "Se enviará la invitación a este correo para que fije su contraseña."
            )
            # La cuenta nace pendiente: el estado se decide al activarla.
            self.fields.pop("is_active")
        else:
            self.fields["email"].required = False
            self.fields["nombre"].initial = self.instance.first_name
            self.fields["apellido"].initial = self.instance.last_name

    def clean_email(self):
        # Dos cadenas vacías chocan contra el índice único; None no.
        return self.cleaned_data.get("email") or None

    def save(self, commit=True):
        usuario = super().save(commit=False)
        usuario.first_name = self.cleaned_data["nombre"]
        usuario.last_name = self.cleaned_data["apellido"]
        if self.creando:
            # Sin contraseña usable y sin acceso hasta que active por correo.
            usuario.is_active = False
            usuario.set_unusable_password()
        if commit:
            usuario.save()
            # `delegaciones_autorizadas` es una relación M2M: se guarda aparte.
            self.save_m2m()
        return usuario


# --------------------------------------------------- Recuperar la contraseña
class RecuperarForm(forms.Form):
    correo = forms.EmailField(label="Correo electrónico")


class CodigoForm(forms.Form):
    codigo = forms.CharField(
        label="Código de verificación",
        max_length=6,
        validators=[RegexValidator(r"^\d{6}$", "El código son 6 dígitos.")],
        widget=forms.TextInput(
            attrs={"class": "codigo", "inputmode": "numeric", "autocomplete": "off"}
        ),
    )


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
