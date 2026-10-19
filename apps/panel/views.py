from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect
from django.utils.http import url_has_allowed_host_and_scheme
from django.views import View
from django.views.generic import TemplateView

from apps.common.delegaciones import CLAVE_SESION, autorizadas
from apps.common.permisos import codigo_de
from apps.panel.servicios import acciones_del_rol, estadisticas


class Inicio(LoginRequiredMixin, TemplateView):
    template_name = "inicio.html"

    def get_context_data(self, **kwargs):
        contexto = super().get_context_data(**kwargs)
        usuario = self.request.user
        contexto["seccion"] = "inicio"
        contexto["codigo_rol"] = codigo_de(usuario)
        contexto["acciones"] = acciones_del_rol(usuario)
        contexto.update(estadisticas(usuario))
        return contexto


class CambiarDelegacion(LoginRequiredMixin, View):
    """Fija la delegación activa de la sesión, validada en el servidor.

    Solo acepta una delegación autorizada; cualquier otra deja el contexto como
    estaba. Sin valor, vuelve al alcance global. Después regresa a la página
    desde la que se pidió, para que listados y filtros se actualicen.
    """

    def post(self, request):
        valor = request.POST.get("delegacion", "")
        if not valor:
            request.session.pop(CLAVE_SESION, None)
        elif autorizadas(request.user).filter(pk=valor).exists():
            request.session[CLAVE_SESION] = int(valor)
        return redirect(self._destino(request))

    @staticmethod
    def _destino(request):
        siguiente = request.POST.get("siguiente") or ""
        if url_has_allowed_host_and_scheme(
            siguiente, allowed_hosts={request.get_host()}, require_https=request.is_secure()
        ):
            return siguiente
        return "panel:inicio"

