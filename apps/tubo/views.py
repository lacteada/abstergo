"""El Tubo de trabajo: mantenedor de tareas y tablero kanban.

El tablero lista cada tarea en la columna de su estado. Mover una tarjeta
(llamar a `Mover`) cambia el estado de la tarea.
"""

from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.views.generic import TemplateView, View

from apps.common.delegaciones import acotar
from apps.common.vistas_base import (
    AltaBase,
    BorradoBase,
    ConsultaBase,
    DesactivarBase,
    EdicionBase,
    ListadoBase,
    PermisoRequeridoMixin,
    ReactivarBase,
)
from apps.cuentas.models import Usuario
from apps.tubo.forms import CartaForm, TareaTuboForm
from apps.tubo.models import ESTADOS, Carta, TareaTubo


class _Tubo:
    model = TareaTubo
    form_class = TareaTuboForm
    seccion = "tubo"
    url_listado = "tubo:tareas"


class Listado(_Tubo, ListadoBase):
    template_name = "tubo/tareas_lista.html"
    titulo = "Compromisos"
    etiqueta_nueva = "Nuevo compromiso"
    busqueda = ("referencia", "titulo", "descripcion", "responsable__first_name")
    relacionadas = ("delegacion", "responsable", "vecino")
    campo_delegacion = "delegacion"
    exportar_nombre = "tubo_tareas"
    exportar_columnas = (
        ("Código", "referencia"),
        ("Título", "titulo"),
        ("Estado", "get_estado_display"),
        ("Delegación", "delegacion.nombre"),
        ("Responsable", "responsable.get_full_name"),
        ("Ingreso", "fecha_ingreso"),
        ("Compromiso", "fecha_compromiso"),
    )
    url_nueva = "tubo:tareas_nueva"


class Alta(_Tubo, AltaBase):
    titulo = "Nuevo compromiso"


class Edicion(_Tubo, EdicionBase):
    titulo = "Editar compromiso"


class Borrado(_Tubo, BorradoBase):
    titulo = "Eliminar compromiso"


class Desactivar(_Tubo, DesactivarBase):
    pass


class Reactivar(_Tubo, ReactivarBase):
    pass


class Consulta(_Tubo, ConsultaBase):
    titulo = "Consultar compromiso"
    consulta_campos = (
        ("Código", "referencia"),
        ("Título", "titulo"),
        ("Descripción", "descripcion"),
        ("Estado", "get_estado_display"),
        ("Tipo", "get_tipo_display"),
        ("Delegación", "delegacion.nombre"),
        ("Territorio", "territorio.nombre"),
        ("Solicitante", "solicitante"),
        ("Responsable", "responsable.get_full_name"),
        ("Apoyo", "apoyo.get_full_name"),
        ("Atención", "atencion.referencia"),
        ("Avance", "avance"),
        ("Vecino", "vecino.nombre"),
        ("Fecha de ingreso", "fecha_ingreso"),
        ("Fecha de compromiso", "fecha_compromiso"),
    )


class Tablero(LoginRequiredMixin, PermisoRequeridoMixin, TemplateView):
    """El kanban: una columna por estado, con las tareas de la delegación."""

    template_name = "tubo/tablero.html"
    model = TareaTubo
    titulo = "Compromisos"
    seccion = "tubo"
    url_listado = "tubo:tablero"

    def get_context_data(self, **kwargs):
        contexto = super().get_context_data(**kwargs)
        tareas = acotar(
            self.request,
            TareaTubo.objects.select_related("responsable", "delegacion"),
            "delegacion",
        )
        columnas = [
            {
                "codigo": codigo,
                "etiqueta": etiqueta,
                "tareas": [tarea for tarea in tareas if tarea.estado == codigo],
            }
            for codigo, etiqueta in ESTADOS
        ]
        contexto.update(
            titulo=self.titulo,
            seccion=self.seccion,
            url_listado="tubo:tablero",
            url_nueva="tubo:tareas_nueva",
            columnas=columnas,
            usuarios=Usuario.vigentes(),
            vencidas=len([tarea for tarea in tareas if tarea.vencida]),
        )
        return contexto


class Historial(LoginRequiredMixin, PermisoRequeridoMixin, TemplateView):
    """El historial de estados de una tarea (RF-018)."""

    template_name = "tubo/historial.html"
    model = TareaTubo
    titulo = "Historial de la tarea"
    seccion = "tubo"
    url_listado = "tubo:tablero"

    def get_context_data(self, **kwargs):
        contexto = super().get_context_data(**kwargs)
        tarea = get_object_or_404(
            TareaTubo.todos.select_related("responsable"), pk=self.kwargs["pk"]
        )
        contexto.update(
            titulo=f"Historial · {tarea.titulo}",
            seccion=self.seccion,
            url_listado=self.url_listado,
            tarea=tarea,
            historial=tarea.historial.select_related("usuario"),
        )
        return contexto


class Mover(LoginRequiredMixin, PermisoRequeridoMixin, View):
    """Cambia el estado de una tarea: el arrastre del kanban."""

    model = TareaTubo

    def post(self, request, pk, *args, **kwargs):
        tarea = get_object_or_404(TareaTubo.todos.all(), pk=pk)
        nuevo = request.POST.get("estado")
        if nuevo not in dict(ESTADOS):
            return JsonResponse({"error": "estado inválido"}, status=400)
        if not tarea.puede_pasar_a(nuevo):
            return JsonResponse({"error": "transición no permitida"}, status=400)
        tarea.estado = nuevo
        tarea._usuario_cambio = request.user
        tarea.save(update_fields=["estado"])
        return JsonResponse({"pk": tarea.pk, "estado": tarea.estado})


class Reasignar(LoginRequiredMixin, PermisoRequeridoMixin, View):
    """Reasigna el funcionario responsable de una tarea (RF-053)."""

    model = TareaTubo

    def post(self, request, pk, *args, **kwargs):
        tarea = get_object_or_404(TareaTubo.todos.all(), pk=pk)
        tarea.responsable_id = request.POST.get("responsable") or None
        tarea.save(update_fields=["responsable"])
        return JsonResponse({"pk": tarea.pk, "responsable": tarea.responsable_id})


# ------------------------------------------------------- Tubo de cartas (RF-054)
class _Cartas:
    model = Carta
    form_class = CartaForm
    titulo = "Tubo de cartas"
    seccion = "tubo"
    url_listado = "tubo:cartas"


class CartasListado(_Cartas, ListadoBase):
    template_name = "tubo/cartas_lista.html"
    etiqueta_nueva = "Nueva carta"
    busqueda = ("referencia", "asunto", "remitente", "destinatario")
    relacionadas = ("delegacion", "encargado")
    campo_delegacion = "delegacion"
    exportar_nombre = "cartas"
    exportar_columnas = (
        ("Código", "referencia"),
        ("Asunto", "asunto"),
        ("Destinatario", "get_destinatario_display"),
        ("Remitente", "remitente"),
        ("Estado", "get_estado_display"),
        ("Fecha", "fecha"),
    )
    url_nueva = "tubo:cartas_nueva"

    def get_context_data(self, **kwargs):
        contexto = super().get_context_data(**kwargs)
        totales = {codigo: 0 for codigo, _ in Carta.ESTADOS}
        for estado in self.get_queryset().values_list("estado", flat=True):
            totales[estado] = totales.get(estado, 0) + 1
        contexto["subtitulo"] = " · ".join(
            f"{etiqueta}: {totales[codigo]}" for codigo, etiqueta in Carta.ESTADOS
        )
        return contexto


class CartasAlta(_Cartas, AltaBase):
    titulo = "Nueva carta"


class CartasEdicion(_Cartas, EdicionBase):
    titulo = "Editar carta"


class CartasBorrado(_Cartas, BorradoBase):
    titulo = "Eliminar carta"


class CartasConsulta(_Cartas, ConsultaBase):
    consulta_campos = (
        ("Código", "referencia"),
        ("Correlativo", "correlativo"),
        ("Asunto", "asunto"),
        ("Destinatario", "get_destinatario_display"),
        ("Remitente", "remitente"),
        ("Contacto", "contacto"),
        ("Estado", "get_estado_display"),
        ("Encargado", "encargado.get_full_name"),
        ("Fecha", "fecha"),
        ("Observación", "observacion"),
    )


class Agenda(_Tubo, ListadoBase):
    """Agenda del delegado: sus compromisos por fecha, con exportación (RF-055)."""

    template_name = "tubo/agenda.html"
    titulo = "Mi agenda"
    etiqueta_nueva = "Nuevo compromiso"
    busqueda = ("referencia", "titulo", "descripcion")
    relacionadas = ("delegacion", "responsable", "territorio")
    campo_delegacion = "delegacion"
    exportar_nombre = "agenda"
    exportar_columnas = (
        ("Código", "referencia"),
        ("Título", "titulo"),
        ("Responsable", "responsable.get_full_name"),
        ("Compromiso", "fecha_compromiso"),
        ("Estado", "get_estado_display"),
        ("Territorio", "territorio.nombre"),
    )
    url_nueva = "tubo:tareas_nueva"
    url_listado = "tubo:agenda"

    def get_queryset(self):
        return super().get_queryset().order_by("fecha_compromiso", "orden")
