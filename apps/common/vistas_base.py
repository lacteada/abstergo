"""Vistas compartidas por los 7 mantenedores.

Cada módulo declara solo sus datos: el modelo, el formulario, el título, la
plantilla y los nombres de sus rutas. El comportamiento vive acá, una vez.
"""

from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q
from django.shortcuts import redirect
from django.urls import reverse
from django.views.generic import CreateView, DeleteView, ListView, UpdateView


class Comun:
    """Datos que cada módulo define y que las plantillas necesitan.

    Arma el contexto una sola vez: los listados usan `url_nueva`, las otras
    vistas la ignoran (queda vacía), así que no hace falta repetir esto en cada
    clase.
    """

    titulo = ""
    subtitulo = ""
    seccion = ""
    etiqueta_nueva = ""
    url_listado = ""
    url_nueva = None  # solo el listado la define

    def get_context_data(self, **kwargs):
        contexto = super().get_context_data(**kwargs)
        contexto.update(
            titulo=self.titulo,
            subtitulo=self.subtitulo,
            seccion=self.seccion,
            etiqueta_nueva=self.etiqueta_nueva,
            url_listado=self.url_listado,
            url_nueva=reverse(self.url_nueva) if self.url_nueva else "",
        )
        return contexto


class ListadoBase(Comun, LoginRequiredMixin, ListView):
    template_name = "listado.html"
    busqueda = ()
    # Llaves foráneas que la plantilla recorre. Traerlas con JOIN evita una
    # consulta por fila.
    relacionadas = ()

    def get_queryset(self):
        queryset = super().get_queryset()
        if self.relacionadas:
            queryset = queryset.select_related(*self.relacionadas)
        q = self.request.GET.get("q")
        if q and self.busqueda:
            condicion = Q()
            for campo in self.busqueda:
                condicion |= Q(**{f"{campo}__icontains": q})
            queryset = queryset.filter(condicion)
        return queryset


class _FormularioBase(Comun, LoginRequiredMixin):
    template_name = "formulario.html"

    def get_success_url(self):
        return reverse(self.url_listado)


class AltaBase(_FormularioBase, CreateView):
    pass


class EdicionBase(_FormularioBase, UpdateView):
    pass


class BorradoBase(Comun, LoginRequiredMixin, DeleteView):
    template_name = "confirmar.html"

    def form_valid(self, form):
        # Las 7 entidades tienen borrado lógico: se marca la fila en vez de
        # borrarla, así nadie pierde sus referencias (el vecino su territorio,
        # el usuario su rol).
        self.object.eliminar()
        return redirect(self.url_listado)
