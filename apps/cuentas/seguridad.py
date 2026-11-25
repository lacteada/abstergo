"""Gestión personal de la credencial; exige reautenticación, no basta una sesión abierta."""

import io
import time

import pyotp
import qrcode
import qrcode.image.svg
from django import forms
from django.conf import settings
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import ImproperlyConfigured
from django.shortcuts import redirect, render
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.cache import never_cache
from django.views.decorators.debug import sensitive_post_parameters

from apps.cuentas import mfa
from apps.cuentas.models import EventoAcceso


class ConfigurarForm(forms.Form):
    password = forms.CharField(label="Contraseña actual", widget=forms.PasswordInput)


@method_decorator(never_cache, name="dispatch")
@method_decorator(sensitive_post_parameters("password", "codigo"), name="dispatch")
class Seguridad(LoginRequiredMixin, View):
    template_name = "cuentas/seguridad.html"

    def pendiente(self, request):
        datos = request.session.get("mfa_alta", {})
        if (
            datos.get("hash") == request.user.get_session_auth_hash()
            and time.time() - datos.get("inicio", 0) < 300
            and datos.get("fallos", 0) < 5
        ):
            return datos
        request.session.pop("mfa_alta", None)
        return None

    def mostrar(self, request, **extra):
        factor = mfa.credencial(request.user)
        contexto = {
            "factor": factor,
            "form": ConfigurarForm(),
            "eventos": EventoAcceso.objects.filter(usuario=request.user)[:12],
            "disponible": bool(settings.MFA_ENCRYPTION_KEY),
        }
        pendiente = self.pendiente(request)
        if pendiente and not (factor and factor.activo):
            secreto = mfa.descifrar(pendiente["secreto"])
            uri = pyotp.TOTP(secreto).provisioning_uri(
                name=request.user.email, issuer_name="Abstergo"
            )
            imagen = qrcode.make(uri, image_factory=qrcode.image.svg.SvgPathImage)
            buffer = io.BytesIO()
            imagen.save(buffer)
            contexto.update(secreto=secreto, qr=buffer.getvalue().decode())
        contexto.update(extra)
        return render(request, self.template_name, contexto)

    def get(self, request):
        return self.mostrar(request)

    def post(self, request):
        accion = request.POST.get("accion")
        if accion == "confirmar":
            pendiente = self.pendiente(request)
            if not pendiente:
                return self.mostrar(
                    request, error="Configuración vencida. Confirma tu contraseña nuevamente."
                )
            codigos = mfa.activar(
                request.user,
                mfa.descifrar(pendiente["secreto"]),
                request.POST.get("codigo", ""),
            )
            if codigos is None:
                pendiente["fallos"] += 1
                request.session["mfa_alta"] = pendiente
                return self.mostrar(request, error=mfa.ERROR_CODIGO)
            request.session.pop("mfa_alta", None)
            mfa.marcar_sesion(request, request.user)
            return self.mostrar(request, codigos=codigos)
        form = ConfigurarForm(request.POST)
        if not form.is_valid() or not request.user.check_password(
            form.cleaned_data.get("password", "")
        ):
            return self.mostrar(request, error="La contraseña actual no es válida.")
        factor = mfa.credencial(request.user)
        if accion == "desactivar" and factor and factor.activo:
            if not mfa.verificar(request.user, request.POST.get("codigo", "")):
                return self.mostrar(request, error=mfa.ERROR_CODIGO)
            mfa.desactivar(request.user)
            mfa.marcar_sesion(request, request.user)
            return redirect("cuentas:seguridad")
        if accion != "preparar" or (factor and factor.activo):
            return self.mostrar(request, error="Acción no disponible.")
        try:
            secreto_cifrado = mfa.cifrar(pyotp.random_base32())
        except ImproperlyConfigured:
            return self.mostrar(
                request, error="El administrador debe configurar la llave de cifrado MFA."
            )
        request.session["mfa_alta"] = {
            "secreto": secreto_cifrado,
            "hash": request.user.get_session_auth_hash(),
            "inicio": time.time(),
            "fallos": 0,
        }
        return self.mostrar(request)
