from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView

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
