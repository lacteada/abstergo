from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView


class Inicio(LoginRequiredMixin, TemplateView):
    template_name = "inicio.html"
    extra_context = {"seccion": "inicio"}
