"""Flujo de acceso web con segundo factor antes de crear la sesión autenticada."""

import time

from django import forms
from django.contrib.auth import get_user_model, login, logout
from django.contrib.auth.views import LoginView
from django.shortcuts import redirect
from django.urls import reverse
from django.utils.crypto import constant_time_compare
from django.utils.decorators import method_decorator
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.cache import never_cache
from django.views.decorators.debug import sensitive_post_parameters
from django.views.generic import FormView

from apps.cuentas import mfa
from apps.cuentas.forms import FormularioLogin


class CodigoSegundoFactor(forms.Form):
    codigo = forms.CharField(
        label="Código del autenticador o de recuperación",
        max_length=32,
        widget=forms.TextInput(attrs={"autocomplete": "one-time-code", "autofocus": True}),
    )


@method_decorator(never_cache, name="dispatch")
class Ingresar(LoginView):
    template_name = "cuentas/login.html"
    authentication_form = FormularioLogin

    def form_valid(self, form):
        usuario = form.get_user()
        factor = mfa.credencial(usuario)
        if factor and factor.activo:
            # Ningún dato protegido ni token se entrega después de la contraseña sola.
            self.request.session.cycle_key()
            self.request.session["mfa_pendiente"] = {
                "usuario": usuario.pk,
                "hash": usuario.get_session_auth_hash(),
                "inicio": time.time(),
                "siguiente": self.get_success_url(),
            }
            return redirect("cuentas:segundo_factor")
        respuesta = super().form_valid(form)
        mfa.marcar_sesion(self.request, usuario)
        mfa.evento(usuario, "Acceso con contraseña")
        return respuesta


@method_decorator(never_cache, name="dispatch")
@method_decorator(sensitive_post_parameters("codigo"), name="dispatch")
class VerificarSegundoFactor(FormView):
    template_name = "cuentas/segundo_factor.html"
    form_class = CodigoSegundoFactor

    def dispatch(self, request, *args, **kwargs):
        pendiente = request.session.get("mfa_pendiente", {})
        self.usuario = (
            get_user_model()
            .objects.filter(
                pk=pendiente.get("usuario"),
                is_active=True,
                eliminado__isnull=True,
            )
            .first()
        )
        if (
            not self.usuario
            or time.time() - pendiente.get("inicio", 0) > 300
            or not constant_time_compare(
                pendiente.get("hash", ""),
                self.usuario.get_session_auth_hash(),
            )
        ):
            request.session.pop("mfa_pendiente", None)
            return redirect("cuentas:login")
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        if not mfa.verificar(self.usuario, form.cleaned_data["codigo"]):
            form.add_error("codigo", mfa.ERROR_CODIGO + " Tras 5 fallos, espera 5 minutos.")
            return self.form_invalid(form)
        pendiente = self.request.session.pop("mfa_pendiente")
        login(self.request, self.usuario, backend="django.contrib.auth.backends.ModelBackend")
        mfa.marcar_sesion(self.request, self.usuario)
        siguiente = pendiente.get("siguiente", "")
        if not url_has_allowed_host_and_scheme(
            siguiente,
            {self.request.get_host()},
            require_https=self.request.is_secure(),
        ):
            siguiente = reverse("panel:inicio")
        return redirect(siguiente)


class ExigirSegundoFactor:
    """Revalida sesiones previas al alta/baja MFA y evita la puerta alternativa del Admin."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.path == "/admin/login/":
            return redirect(reverse("cuentas:login") + "?next=/admin/")
        if request.user.is_authenticated and not request.path.startswith("/api/"):
            if request.session.get("mfa_version", 0) != mfa.version(request.user):
                logout(request)
                return redirect("cuentas:login")
        return self.get_response(request)
