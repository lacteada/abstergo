from django.conf import settings
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.views.generic import FormView, TemplateView, View

from apps.common.vistas_base import AltaBase, BorradoBase, EdicionBase, ListadoBase
from apps.cuentas import otp
from apps.cuentas.forms import (
    CodigoForm,
    NuevaPasswordForm,
    RecuperarForm,
    RolForm,
    UsuarioForm,
)
from apps.cuentas.models import Rol, Usuario


# ------------------------------------------------------------------ Roles
class RolesListado(ListadoBase):
    model = Rol
    template_name = "cuentas/roles_lista.html"
    titulo = "Roles"
    seccion = "roles"
    etiqueta_nueva = "Nuevo rol"
    busqueda = ("codigo", "nombre", "descripcion")
    exportar_nombre = "roles"
    exportar_columnas = (
        ("Código", "codigo"),
        ("Nombre", "nombre"),
        ("Descripción", "descripcion"),
    )
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
    auditar_lectura = True
    exportar_nombre = "usuarios"
    exportar_columnas = (
        ("Nombre", "get_full_name"),
        ("Correo", "email"),
        ("Rol", "rol.nombre"),
        ("Delegación", "delegacion.nombre"),
        ("Activo", lambda u: "Sí" if u.is_active else "No"),
    )
    url_nueva = "cuentas:usuarios_nueva"
    url_listado = "cuentas:usuarios"

    def get_queryset(self):
        # El listado agrega la búsqueda, así que no puede partir de `vigentes()`.
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
class Recuperar(FormView):
    template_name = "cuentas/recuperar.html"
    form_class = RecuperarForm
    success_url = reverse_lazy("cuentas:validar")

    def form_valid(self, form):
        correo = form.cleaned_data["correo"]
        otp.solicitar(correo)
        # El correo queda en la sesión solo para no volver a pedirlo. El código,
        # en cambio, vive en la tabla.
        self.request.session["recuperacion_correo"] = correo
        return super().form_valid(form)


class Validar(FormView):
    template_name = "cuentas/validar.html"
    form_class = CodigoForm
    success_url = reverse_lazy("cuentas:nueva_password")

    def dispatch(self, request, *args, **kwargs):
        if not request.session.get("recuperacion_correo"):
            return redirect("cuentas:recuperar")
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        contexto = super().get_context_data(**kwargs)
        contexto["correo"] = self.request.session.get("recuperacion_correo", "")
        contexto["minutos"] = settings.OTP_EXPIRY_MINUTES
        return contexto

    def form_valid(self, form):
        errores = otp.verificar(
            self.request.session["recuperacion_correo"], form.cleaned_data["codigo"]
        )
        if errores:
            form.add_error(None, errores)
            return self.form_invalid(form)
        return super().form_valid(form)


class Reenviar(View):
    def post(self, request):
        correo = request.session.get("recuperacion_correo")
        if correo:
            otp.solicitar(correo)
        return redirect("cuentas:validar")


class NuevaPassword(FormView):
    template_name = "cuentas/nueva_password.html"
    form_class = NuevaPasswordForm
    success_url = reverse_lazy("cuentas:login")

    def dispatch(self, request, *args, **kwargs):
        correo = request.session.get("recuperacion_correo")
        if not correo or not otp.hay_codigo_validado(correo):
            return redirect("cuentas:recuperar")
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        correo = self.request.session.get("recuperacion_correo")
        errores = otp.restablecer(correo, form.cleaned_data["password1"])
        if errores:
            form.add_error(None, errores)
            return self.form_invalid(form)
        self.request.session.pop("recuperacion_correo", None)
        return super().form_valid(form)


class Privacidad(TemplateView):
    """Política de privacidad, pública y enlazada desde el login."""

    template_name = "privacidad.html"
