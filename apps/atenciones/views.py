from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.views import View

from apps.atenciones.forms import AtencionForm
from apps.atenciones.models import Atencion
from apps.ciudadanos.models import Vecino
from apps.common.validators import normalizar_rut
from apps.common.vistas_base import BorradoBase, EdicionBase, ListadoBase
from apps.cumplimiento.auditoria import registrar


def buscar_vecinos(rut="", nombre="", apellido=""):
    """Busca por RUT (normalizado) o por nombre y apellido."""
    if rut:
        return Vecino.objects.filter(rut__iexact=normalizar_rut(rut))
    condiciones = Q()
    if nombre:
        condiciones &= Q(nombre__icontains=nombre)
    if apellido:
        condiciones &= Q(nombre__icontains=apellido)
    if not condiciones:
        return Vecino.objects.none()
    return Vecino.objects.filter(condiciones)


class Listado(ListadoBase):
    model = Atencion
    template_name = "atenciones/atenciones_lista.html"
    titulo = "Atenciones"
    seccion = "atenciones"
    etiqueta_nueva = "Crear Atención"
    busqueda = ("vecino__nombre", "vecino__rut", "motivo", "tipo_atencion__nombre")
    relacionadas = (
        "vecino",
        "tipo_atencion",
        "sub_atencion",
        "delegacion",
        "funcionario",
    )
    url_nueva = "atenciones:crear"
    url_listado = "atenciones:listado"
    auditar_lectura = True
    exportar_nombre = "atenciones"
    exportar_columnas = (
        ("Fecha", lambda a: a.fecha.strftime("%d-%m-%Y %H:%M") if a.fecha else ""),
        ("Vecino", "vecino.nombre"),
        ("RUT", "vecino.rut"),
        ("Tipo", "tipo_atencion.nombre"),
        ("Sub atención", "sub_atencion.nombre"),
        ("Delegación", "delegacion.nombre"),
        ("Funcionario", "funcionario.get_full_name"),
        ("Estado", "get_estado_display"),
        ("Motivo", "motivo"),
    )


class CrearAtencion(LoginRequiredMixin, View):
    """El flujo del rol Funcionario: buscar al vecino y registrar la atención.

    La búsqueda es por GET (funciona sin JavaScript); el alta por POST. Si el
    vecino no existe, la plantilla ofrece agregarlo.
    """

    template_name = "atenciones/crear.html"

    def get(self, request):
        return render(request, self.template_name, self._contexto(request))

    def post(self, request):
        vecino = get_object_or_404(Vecino, pk=request.POST.get("vecino"))
        form = AtencionForm(request.POST)
        if form.is_valid():
            atencion = form.save(commit=False)
            atencion.vecino = vecino
            atencion.funcionario = request.user
            atencion.delegacion = request.user.delegacion or vecino.territorio
            atencion.save()
            registrar(request, "crear", atencion, "Alta desde Crear Atención")
            messages.success(request, f"Atención registrada para {vecino.nombre}.")
            return redirect("atenciones:listado")
        return render(
            request,
            self.template_name,
            self._contexto(request, form=form, vecino=vecino),
        )

    def _contexto(self, request, form=None, vecino=None):
        busqueda = {
            "rut": request.GET.get("rut", "").strip(),
            "nombre": request.GET.get("nombre", "").strip(),
            "apellido": request.GET.get("apellido", "").strip(),
        }
        buscado = any(busqueda.values())
        encontrados = Vecino.objects.none()
        if buscado:
            encontrados = buscar_vecinos(**busqueda)
            if vecino is None and encontrados.count() == 1:
                vecino = encontrados.first()
        if vecino is not None:
            registrar(request, "ver", vecino, "Acceso al historial del vecino")
        return {
            "seccion": "atenciones",
            "busqueda": busqueda,
            "buscado": buscado,
            "encontrados": encontrados,
            "vecino": vecino,
            "historial": vecino.atenciones.all() if vecino else [],
            "form": form or AtencionForm(),
        }


class Edicion(EdicionBase):
    model = Atencion
    form_class = AtencionForm
    titulo = "Editar atención"
    seccion = "atenciones"
    url_listado = "atenciones:listado"


class Borrado(BorradoBase):
    model = Atencion
    titulo = "Eliminar atención"
    seccion = "atenciones"
    url_listado = "atenciones:listado"
