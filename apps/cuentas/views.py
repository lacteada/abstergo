from django.conf import settings
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.views.generic import FormView, TemplateView, View

from apps.common.vistas_base import (
    AltaBase,
    BorradoBase,
    ConsultaBase,
    EdicionBase,
    ListadoBase,
    PermisoRequeridoMixin,
    ReactivarBase,
)
from apps.cuentas import invitaciones, otp
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
    busqueda = ("referencia", "codigo", "nombre", "descripcion")
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


class RolesReactivar(ReactivarBase):
    model = Rol
    titulo = "Rol"
    seccion = "roles"
    url_listado = "cuentas:roles"


class RolesConsulta(ConsultaBase):
    model = Rol
    titulo = "Consultar rol"
    seccion = "roles"
    url_listado = "cuentas:roles"
    consulta_campos = (
        ("Código", "referencia"),
        ("Clave", "codigo"),
        ("Nombre", "nombre"),
        ("Descripción", "descripcion"),
    )


# --------------------------------------------------------------- Usuarios
class UsuariosListado(ListadoBase):
    model = Usuario
    template_name = "cuentas/usuarios_lista.html"
    titulo = "Usuarios"
    seccion = "usuarios"
    etiqueta_nueva = "Nuevo usuario"
    busqueda = ("referencia", "first_name", "last_name", "email")
    relacionadas = ("rol", "delegacion")
    campo_delegacion = "delegacion"
    auditar_lectura = True
    exportar_nombre = "usuarios"
    exportar_columnas = (
        ("Nombre", "get_full_name"),
        ("Correo", "email"),
        ("Rol", "rol.nombre"),
        ("Delegación", "delegacion.nombre"),
        ("Delegaciones autorizadas", "delegaciones_texto"),
        ("Activo", lambda u: "Sí" if u.is_active else "No"),
    )
    url_nueva = "cuentas:usuarios_nueva"
    url_listado = "cuentas:usuarios"

    def get_queryset(self):
        return super().get_queryset()


class UsuariosAlta(AltaBase):
    model = Usuario
    form_class = UsuarioForm
    titulo = "Nuevo usuario"
    seccion = "usuarios"
    url_listado = "cuentas:usuarios"
    # El aviso lo arma la vista, porque depende del envío de la invitación.
    mensaje_alta = ""

    def form_valid(self, form):
        respuesta = super().form_valid(form)
        if invitaciones.enviar(self.object, self.request):
            messages.success(
                self.request,
                f"Cuenta creada. Se envió la invitación a {self.object.email}.",
            )
        else:
            messages.error(
                self.request,
                "Cuenta creada, pero no se pudo enviar la invitación. Reenvíala "
                "desde el listado.",
            )
        return respuesta


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


class UsuariosReactivar(ReactivarBase):
    model = Usuario
    titulo = "Usuario"
    seccion = "usuarios"
    url_listado = "cuentas:usuarios"


class UsuariosConsulta(ConsultaBase):
    model = Usuario
    titulo = "Consultar usuario"
    seccion = "usuarios"
    url_listado = "cuentas:usuarios"
    consulta_campos = (
        ("Código", "referencia"),
        ("Nombre", "get_full_name"),
        ("Correo", "email"),
        ("Rol", "rol.nombre"),
        ("Delegación", "delegacion.nombre"),
        ("Delegaciones autorizadas", "delegaciones_texto"),
        ("Estado", "estado_texto"),
    )


class UsuariosInvitar(LoginRequiredMixin, PermisoRequeridoMixin, View):
    """Reenvía la invitación a una cuenta que todavía no se activó.

    Como el administrador no define la contraseña, este es el camino para
    recuperar una invitación perdida sin tener que dar de baja la cuenta.
    """

    model = Usuario

    def post(self, request, pk):
        usuario = get_object_or_404(Usuario.vigentes(), pk=pk)
        if not usuario.pendiente:
            messages.warning(request, "La cuenta ya está activada.")
        elif invitaciones.enviar(usuario, request):
            messages.success(request, f"Invitación reenviada a {usuario.email}.")
        else:
            messages.error(request, "No se pudo enviar la invitación.")
        return redirect("cuentas:usuarios")


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
            espera = otp.reenviar(correo)
            if espera:
                messages.warning(
                    request,
                    f"Espera {espera} segundos antes de pedir otro código.",
                )
            else:
                messages.success(request, "Enviamos un código nuevo.")
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


# ---------------------------------------------------- Activar una cuenta
class Activar(FormView):
    """Fija la contraseña de una cuenta invitada y la activa.

    El enlace lleva el identificador y un token firmado con la contraseña
    actual; al guardar, el token deja de valer, así que sirve una sola vez. Un
    enlace usado o vencido muestra el aviso de inválido.
    """

    template_name = "cuentas/activar.html"
    form_class = NuevaPasswordForm
    success_url = reverse_lazy("cuentas:login")

    def dispatch(self, request, *args, **kwargs):
        self.usuario = invitaciones.usuario_de_enlace(kwargs["uidb64"])
        self.valido = invitaciones.enlace_valido(self.usuario, kwargs["token"])
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        contexto = super().get_context_data(**kwargs)
        contexto["valido"] = self.valido
        contexto["nombre"] = self.usuario.first_name if self.usuario else ""
        return contexto

    def form_valid(self, form):
        if not self.valido:
            return self.form_invalid(form)
        self.usuario.set_password(form.cleaned_data["password1"])
        self.usuario.is_active = True
        self.usuario.save(update_fields=["password", "is_active"])
        messages.success(
            self.request, "Tu cuenta quedó activa. Ya puedes iniciar sesión."
        )
        return super().form_valid(form)
