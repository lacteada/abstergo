"""El Tubo de trabajo: mantenedor de tareas y tablero kanban.

El tablero lista cada tarea en la columna de su estado. Mover una tarjeta
(llamar a `Mover`) cambia el estado de la tarea.
"""

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import Http404, JsonResponse
from django.shortcuts import get_object_or_404, redirect
from django.views.generic import TemplateView, View

from apps.atenciones.models import Atencion
from apps.common.delegaciones import acotar, campo_delegacion_de
from apps.common.permisos import puede
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
from apps.cumplimiento.auditoria import registrar
from apps.sgr.models import RegistroGestion
from apps.tubo import servicios
from apps.tubo.forms import CartaForm, TareaTuboForm
from apps.tubo.models import ESTADOS, Carta, TareaTubo

# Origen del paso manual al tubo: slug -> (modelo de origen, fábrica).
ORIGENES = {
    "atencion": (Atencion, servicios.desde_atencion),
    "carta": (Carta, servicios.desde_carta),
    "actividad": (RegistroGestion, servicios.desde_registro),
}


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

    # El tablero rotula y colorea las columnas; el modelo usa singular.
    ETIQUETAS = {
        "ingresada": "Ingresados",
        "pendiente": "Pendientes",
        "en_proceso": "En proceso",
        "realizada": "Realizados",
    }
    COLORES = {
        "ingresada": "gris",
        "pendiente": "rojo",
        "en_proceso": "ambar",
        "realizada": "verde",
    }

    def get_context_data(self, **kwargs):
        contexto = super().get_context_data(**kwargs)
        tareas = list(
            acotar(
                self.request,
                TareaTubo.objects.select_related(
                    "responsable", "delegacion", "apoyo", "atencion"
                ),
                "delegacion",
            )
        )
        columnas = []
        for numero, (codigo, etiqueta) in enumerate(ESTADOS, start=1):
            en_columna = [tarea for tarea in tareas if tarea.estado == codigo]
            columnas.append(
                {
                    "codigo": codigo,
                    "etiqueta": self.ETIQUETAS.get(codigo, etiqueta),
                    "numero": numero,
                    "color": self.COLORES.get(codigo, ""),
                    "tareas": en_columna,
                    # Las vencidas se cuentan por columna para avisar en la cabecera.
                    "atrasadas": len([tarea for tarea in en_columna if tarea.vencida]),
                }
            )
        total = len(tareas)
        realizadas = len([tarea for tarea in tareas if tarea.estado == "realizada"])
        tasa = (realizadas * 100 / total) if total else 0
        contexto.update(
            titulo=self.titulo,
            seccion=self.seccion,
            url_listado="tubo:tablero",
            url_nueva="tubo:tareas_nueva",
            columnas=columnas,
            usuarios=Usuario.vigentes(),
            puede_escribir=puede(self.request.user, "tasks", escritura=True),
            vencidas=len([tarea for tarea in tareas if tarea.vencida]),
            kpis=[
                {
                    "titulo": "GESTIONES EN TUBO",
                    "numero": total,
                    "subtitulo": "Derivadas para seguimiento",
                    "color": "rojo",
                },
                {
                    "titulo": "REALIZADAS / CONCLUIDAS",
                    "numero": realizadas,
                    "subtitulo": f"Tasa de resolución: {tasa:.1f}%".replace(".", ","),
                    "color": "verde",
                },
                {
                    "titulo": "EN PROCESO ACTIVO",
                    "numero": len([t for t in tareas if t.estado == "en_proceso"]),
                    "subtitulo": "Con cuadrilla o área de apoyo",
                    "color": "ambar",
                },
                {
                    "titulo": "PENDIENTES / ALERTA",
                    "numero": len([t for t in tareas if t.estado == "pendiente"]),
                    "subtitulo": "Esperando gestión técnica",
                    "color": "rojo",
                },
            ],
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
            acotar(
                self.request,
                TareaTubo.todos.select_related("responsable"),
                campo_delegacion_de(TareaTubo),
            ),
            pk=self.kwargs["pk"],
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
    """Cambia el estado de una tarea y reordena su columna (arrastre del kanban)."""

    model = TareaTubo

    def post(self, request, pk, *args, **kwargs):
        tarea = get_object_or_404(
            acotar(request, TareaTubo.todos.all(), campo_delegacion_de(TareaTubo)), pk=pk
        )
        nuevo = request.POST.get("estado")
        if nuevo not in dict(ESTADOS):
            return JsonResponse({"error": "estado inválido"}, status=400)
        if not tarea.puede_pasar_a(nuevo):
            return JsonResponse({"error": "transición no permitida"}, status=400)
        if tarea.estado != nuevo:
            tarea.estado = nuevo
            tarea._usuario_cambio = request.user
            tarea.save(update_fields=["estado"])
        self._reordenar(request, nuevo)
        return JsonResponse({"pk": tarea.pk, "estado": tarea.estado})

    @staticmethod
    def _reordenar(request, estado):
        """Guarda el orden de la columna tal como llega del tablero."""
        pks = [
            int(valor)
            for valor in request.POST.get("orden", "").split(",")
            if valor.isdigit()
        ]
        if not pks:
            return
        columna = acotar(
            request,
            TareaTubo.todos.filter(estado=estado),
            campo_delegacion_de(TareaTubo),
        )
        for posicion, pk in enumerate(pks, start=1):
            columna.filter(pk=pk).update(orden=posicion)


class EnviarAlTubo(LoginRequiredMixin, PermisoRequeridoMixin, View):
    """Crea a mano un compromiso desde una atención, una carta o una actividad."""

    model = TareaTubo

    def post(self, request, origen, pk):
        entrada = ORIGENES.get(origen)
        if entrada is None:
            raise Http404("Origen desconocido.")
        modelo, fabrica = entrada
        gestor = getattr(modelo, "todos", modelo.objects)
        objeto = get_object_or_404(
            acotar(request, gestor.all(), campo_delegacion_de(modelo)), pk=pk
        )
        tarea, creado = fabrica(objeto, request.user)
        registrar(request, "crear", tarea, f"Compromiso creado desde {origen}.")
        if creado:
            messages.success(
                request, f"Compromiso {tarea.referencia} creado en el tubo."
            )
        else:
            messages.info(request, f"{tarea.referencia} ya estaba en el tubo.")
        return redirect("tubo:tareas")


class Reasignar(LoginRequiredMixin, PermisoRequeridoMixin, View):
    """Reasigna el funcionario responsable de una tarea (RF-053)."""

    model = TareaTubo

    def post(self, request, pk, *args, **kwargs):
        tarea = get_object_or_404(
            acotar(request, TareaTubo.todos.all(), campo_delegacion_de(TareaTubo)), pk=pk
        )
        tarea.responsable_id = request.POST.get("responsable") or None
        tarea.save(update_fields=["responsable"])
        return JsonResponse({"pk": tarea.pk, "responsable": tarea.responsable_id})


# ------------------------------------------------------- Tubo de cartas (RF-054)
class _Cartas:
    model = Carta
    form_class = CartaForm
    titulo = "Tubo de cartas"
    seccion = "tubo_cartas"
    url_listado = "tubo:cartas"


class CartasListado(_Cartas, ListadoBase):
    template_name = "tubo/cartas_lista.html"
    etiqueta_nueva = "Nueva carta"
    busqueda = ("referencia", "asunto", "remitente", "destinatario", "tipo")
    relacionadas = ("delegacion", "encargado")
    exportar_nombre = "cartas"
    exportar_columnas = (
        ("Código", "referencia"),
        ("Asunto", "asunto"),
        ("Tipo", "get_tipo_display"),
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


class CartasDesactivar(_Cartas, DesactivarBase):
    titulo = "Carta"


class CartasReactivar(_Cartas, ReactivarBase):
    titulo = "Carta"


class CartasTablero(LoginRequiredMixin, PermisoRequeridoMixin, TemplateView):
    """El kanban de cartas: una columna por estado (RF-054)."""

    template_name = "tubo/cartas_tablero.html"
    model = Carta
    titulo = "Tubo de cartas"
    seccion = "tubo_cartas"
    url_listado = "tubo:cartas"

    # El paso hacia adelante de cada carta (no_aplica queda sin acción).
    COLORES = {
        "en_proceso": "ambar",
        "aprobada": "verde",
        "finalizada": "verde",
        "no_aplica": "gris",
    }
    ACCION_SIGUIENTE = {"en_proceso": "aprobada", "aprobada": "finalizada"}
    ACCION_ETIQUETA = {"aprobada": "Aprobar", "finalizada": "Finalizar"}

    def get_context_data(self, **kwargs):
        contexto = super().get_context_data(**kwargs)
        cartas = list(
            acotar(
                self.request,
                Carta.objects.select_related("delegacion", "encargado"),
                "delegacion",
            )
        )
        columnas = []
        for numero, (codigo, etiqueta) in enumerate(Carta.ESTADOS, start=1):
            en_columna = [carta for carta in cartas if carta.estado == codigo]
            columnas.append(
                {
                    "codigo": codigo,
                    "etiqueta": etiqueta,
                    "numero": numero,
                    "color": self.COLORES.get(codigo, ""),
                    "cartas": [
                        {
                            "carta": carta,
                            "accion": self.ACCION_SIGUIENTE.get(carta.estado, ""),
                            "accion_etiqueta": self.ACCION_ETIQUETA.get(
                                self.ACCION_SIGUIENTE.get(carta.estado, ""), ""
                            ),
                        }
                        for carta in en_columna
                    ],
                }
            )
        contexto.update(
            titulo=self.titulo,
            seccion=self.seccion,
            url_listado=self.url_listado,
            url_nueva="tubo:cartas_nueva",
            columnas=columnas,
            total=len(cartas),
            puede_escribir=puede(self.request.user, "tasks", escritura=True),
        )
        return contexto


class CartaMover(LoginRequiredMixin, PermisoRequeridoMixin, View):
    """Cambia el estado de una carta: el arrastre o el botón del kanban."""

    model = Carta

    def post(self, request, pk, *args, **kwargs):
        carta = get_object_or_404(
            acotar(request, Carta.todos.all(), campo_delegacion_de(Carta)), pk=pk
        )
        nuevo = request.POST.get("estado")
        if nuevo not in dict(Carta.ESTADOS):
            return JsonResponse({"error": "estado inválido"}, status=400)
        carta.estado = nuevo
        carta.save(update_fields=["estado"])
        registrar(request, "editar", carta, "Cambio de estado (kanban de cartas)")
        return JsonResponse({"pk": carta.pk, "estado": carta.estado})


class CartasConsulta(_Cartas, ConsultaBase):
    consulta_tubo = (("carta", "Enviar al tubo"),)
    consulta_campos = (
        ("Código", "referencia"),
        ("Correlativo", "correlativo"),
        ("Asunto", "asunto"),
        ("Tipo", "get_tipo_display"),
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
