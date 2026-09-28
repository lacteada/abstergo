import secrets
from datetime import timedelta

from django.conf import settings
from django.core.mail import send_mail
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.utils import timezone
from django.views.generic import FormView, View

from apps.cuentas.forms import (
    CodigoForm,
    NuevaPasswordForm,
    RecuperarForm,
    RolForm,
    UsuarioForm,
)
from apps.cuentas.models import Rol, Usuario
from apps.common.vistas_base import AltaBase, BorradoBase, EdicionBase, ListadoBase


# ------------------------------------------------------------------ Roles
class RolesListado(ListadoBase):
    model = Rol
    template_name = "cuentas/roles_lista.html"
    titulo = "Roles"
    seccion = "roles"
    etiqueta_nueva = "Nuevo rol"
    busqueda = ("nombre", "descripcion")
    url_nueva = "cuentas:roles_nueva"
    url_listado = "cuentas:roles"


class RolesAlta(AltaBase):
    model = Rol
    form_class = RolForm
    titulo = "Nuevo rol"
    seccion = "roles"
    url_listado = "cuentas:roles"


class RolesEdicion(EdicionBase):
    model = Rol
    form_class = RolForm
    titulo = "Editar rol"
    seccion = "roles"
    url_listado = "cuentas:roles"


class RolesBorrado(BorradoBase):
    model = Rol
    titulo = "Eliminar rol"
    seccion = "roles"
    url_listado = "cuentas:roles"


# --------------------------------------------------------------- Usuarios
class UsuariosListado(ListadoBase):
    model = Usuario
    template_name = "cuentas/usuarios_lista.html"
    titulo = "Usuarios"
    seccion = "usuarios"
    etiqueta_nueva = "Nuevo usuario"
    busqueda = ("first_name", "last_name", "email")
    relacionadas = ("rol", "delegacion")
    url_nueva = "cuentas:usuarios_nueva"
    url_listado = "cuentas:usuarios"

    def get_queryset(self):
        # Usuario conserva el UserManager, que no filtra por borrado lógico.
        return super().get_queryset().filter(eliminado__isnull=True)


class UsuariosAlta(AltaBase):
    model = Usuario
    form_class = UsuarioForm
    titulo = "Nuevo usuario"
    seccion = "usuarios"
    url_listado = "cuentas:usuarios"


class UsuariosEdicion(EdicionBase):
    model = Usuario
    form_class = UsuarioForm
    titulo = "Editar usuario"
    seccion = "usuarios"
    url_listado = "cuentas:usuarios"


class UsuariosBorrado(BorradoBase):
    model = Usuario
    titulo = "Eliminar usuario"
    seccion = "usuarios"
    url_listado = "cuentas:usuarios"


# ------------------------------------------------- Recuperar la contraseña
def _guardar_otp(request, usuario):
    """Genera el código, lo deja en la sesión y lo manda por correo.

    En la sesión, así no necesita tabla propia y no se puede reutilizar.
    """
    codigo = f"{secrets.randbelow(1000000):06d}"
    sesion = request.session
    sesion["otp_codigo"] = codigo
    sesion["otp_usuario"] = usuario.pk
    sesion["otp_expira"] = (
        timezone.now() + timedelta(minutes=settings.OTP_EXPIRY_MINUTES)
    ).timestamp()
    sesion.pop("otp_validado", None)
    send_mail(
        "Código de verificación",
        f"Tu código de verificación es {codigo}. "
        f"Vence en {settings.OTP_EXPIRY_MINUTES} minutos.",
        None,
        [usuario.email],
    )


class Recuperar(FormView):
    template_name = "cuentas/recuperar.html"
    form_class = RecuperarForm
    success_url = reverse_lazy("cuentas:validar")

    def form_valid(self, form):
        usuario = Usuario.objects.filter(
            email__iexact=form.cleaned_data["correo"]
        ).first()
        if usuario:
            _guardar_otp(self.request, usuario)
        # Se siga o no, la respuesta es la misma: no se revela qué correos existen.
        return super().form_valid(form)


class Validar(FormView):
    template_name = "cuentas/validar.html"
    form_class = CodigoForm
    success_url = reverse_lazy("cuentas:nueva_password")

    def dispatch(self, request, *args, **kwargs):
        if "otp_codigo" not in request.session:
            return redirect("cuentas:recuperar")
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        contexto = super().get_context_data(**kwargs)
        usuario = Usuario.objects.filter(
            pk=self.request.session.get("otp_usuario")
        ).first()
        contexto["correo"] = usuario.email if usuario else ""
        contexto["minutos"] = settings.OTP_EXPIRY_MINUTES
        return contexto

    def form_valid(self, form):
        sesion = self.request.session
        if timezone.now().timestamp() > sesion.get("otp_expira", 0):
            form.add_error(None, "El código venció. Pide uno nuevo.")
            return self.form_invalid(form)
        if form.cleaned_data["codigo"] != sesion["otp_codigo"]:
            form.add_error(None, "El código no coincide.")
            return self.form_invalid(form)
        # Se borra de la sesión: sirve una sola vez.
        del sesion["otp_codigo"]
        sesion["otp_validado"] = True
        return super().form_valid(form)


class Reenviar(View):
    def post(self, request):
        usuario = Usuario.objects.filter(pk=request.session.get("otp_usuario")).first()
        if usuario:
            _guardar_otp(request, usuario)
        return redirect("cuentas:validar")


class NuevaPassword(FormView):
    template_name = "cuentas/nueva_password.html"
    form_class = NuevaPasswordForm
    success_url = reverse_lazy("cuentas:login")

    def dispatch(self, request, *args, **kwargs):
        if not request.session.get("otp_validado"):
            return redirect("cuentas:recuperar")
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        usuario = Usuario.objects.filter(
            pk=self.request.session.get("otp_usuario")
        ).first()
        if usuario:
            usuario.set_password(form.cleaned_data["password1"])
            usuario.save()
        for llave in ("otp_usuario", "otp_validado", "otp_expira"):
            self.request.session.pop(llave, None)
        return super().form_valid(form)
