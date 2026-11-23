"""Mantenedores y tablero de la Matriz SGR.

Cada recurso declara un mixin con su modelo, formulario y rutas; las acciones
del CRUD se arman encima y comparten el comportamiento de `vistas_base.py`.
"""

from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404
from django.views.generic import TemplateView

from apps.common import periodo as contexto_periodo
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
from apps.sgr import servicios
from apps.sgr.forms import (
    AjusteConductaForm,
    AlertaForm,
    AreaForm,
    AusenciaForm,
    ComentarioForm,
    EvidenciaForm,
    IndicadorForm,
    MetaIndicadorForm,
    PeriodoForm,
    RegistroGestionForm,
    ValidacionForm,
)
from apps.sgr.models import (
    AjusteConducta,
    Alerta,
    Area,
    Ausencia,
    Comentario,
    Evidencia,
    Indicador,
    MetaIndicador,
    Periodo,
    RegistroGestion,
    Validacion,
)


# --------------------------------------------------------------- Períodos
class _Periodos:
    model = Periodo
    form_class = PeriodoForm
    titulo = "Períodos"
    seccion = "sgr_periodos"
    url_listado = "sgr:periodos"


class PeriodosListado(_Periodos, ListadoBase):
    template_name = "sgr/periodos_lista.html"
    etiqueta_nueva = "Nuevo período"
    busqueda = ("referencia", "codigo", "nombre")
    exportar_nombre = "periodos"
    exportar_columnas = (
        ("Código", "referencia"),
        ("Nombre", "nombre"),
        ("Inicio", "inicio"),
        ("Término", "termino"),
        ("Días", "dias_totales"),
        ("Estado", "get_estado_display"),
    )
    url_nueva = "sgr:periodos_nueva"


class PeriodosAlta(_Periodos, AltaBase):
    titulo = "Nuevo período"


class PeriodosEdicion(_Periodos, EdicionBase):
    titulo = "Editar período"


class PeriodosBorrado(_Periodos, BorradoBase):
    titulo = "Eliminar período"


class PeriodosDesactivar(_Periodos, DesactivarBase):
    pass


class PeriodosReactivar(_Periodos, ReactivarBase):
    pass


class PeriodosConsulta(_Periodos, ConsultaBase):
    consulta_campos = (
        ("Código", "referencia"),
        ("Clave", "codigo"),
        ("Nombre", "nombre"),
        ("Inicio", "inicio"),
        ("Término", "termino"),
        ("Días", "dias_totales"),
        ("Estado", "get_estado_display"),
    )


# ------------------------------------------------------------------- Áreas
class _Areas:
    model = Area
    form_class = AreaForm
    titulo = "Áreas"
    seccion = "sgr_areas"
    url_listado = "sgr:areas"


class AreasListado(_Areas, ListadoBase):
    template_name = "sgr/areas_lista.html"
    etiqueta_nueva = "Nueva área"
    busqueda = ("referencia", "codigo", "nombre", "cargo__nombre", "responsable__first_name")
    relacionadas = ("cargo", "responsable", "delegacion")
    exportar_nombre = "areas"
    exportar_columnas = (
        ("Código", "referencia"),
        ("Nombre", "nombre"),
        ("Grupo", "get_grupo_display"),
        ("Cargo", "cargo.nombre"),
        ("Responsable", "responsable.get_full_name"),
        ("Delegación", "delegacion.nombre"),
        ("Estado", "get_estado_display"),
    )
    url_nueva = "sgr:areas_nueva"


class AreasAlta(_Areas, AltaBase):
    titulo = "Nueva área"


class AreasEdicion(_Areas, EdicionBase):
    titulo = "Editar área"


class AreasBorrado(_Areas, BorradoBase):
    titulo = "Eliminar área"


class AreasDesactivar(_Areas, DesactivarBase):
    pass


class AreasReactivar(_Areas, ReactivarBase):
    pass


class AreasConsulta(_Areas, ConsultaBase):
    consulta_campos = (
        ("Código", "referencia"),
        ("Nombre", "nombre"),
        ("Grupo", "get_grupo_display"),
        ("Cargo", "cargo.nombre"),
        ("Responsable", "responsable.get_full_name"),
        ("Delegación", "delegacion.nombre"),
        ("Estado", "get_estado_display"),
    )


# ------------------------------------------------------------- Indicadores
class _Indicadores:
    model = Indicador
    form_class = IndicadorForm
    titulo = "Indicadores"
    seccion = "sgr_indicadores"
    url_listado = "sgr:indicadores"


class IndicadoresListado(_Indicadores, ListadoBase):
    template_name = "sgr/indicadores_lista.html"
    etiqueta_nueva = "Nuevo indicador"
    busqueda = ("referencia", "codigo", "nombre")
    exportar_nombre = "indicadores"
    exportar_columnas = (
        ("Código", "referencia"),
        ("Nombre", "nombre"),
        ("Grupo", "get_grupo_display"),
        ("Unidad", "get_unidad_display"),
        ("Estado", "get_estado_display"),
    )
    url_nueva = "sgr:indicadores_nueva"


class IndicadoresAlta(_Indicadores, AltaBase):
    titulo = "Nuevo indicador"


class IndicadoresEdicion(_Indicadores, EdicionBase):
    titulo = "Editar indicador"


class IndicadoresBorrado(_Indicadores, BorradoBase):
    titulo = "Eliminar indicador"


class IndicadoresDesactivar(_Indicadores, DesactivarBase):
    pass


class IndicadoresReactivar(_Indicadores, ReactivarBase):
    pass


class IndicadoresConsulta(_Indicadores, ConsultaBase):
    consulta_campos = (
        ("Código", "referencia"),
        ("Nombre", "nombre"),
        ("Grupo", "get_grupo_display"),
        ("Unidad", "get_unidad_display"),
        ("Estado", "get_estado_display"),
    )


# ----------------------------------------------- Metas por área e indicador
class _Metas:
    model = MetaIndicador
    form_class = MetaIndicadorForm
    titulo = "Metas de indicador"
    seccion = "sgr_metas"
    url_listado = "sgr:metas"


class MetasListado(_Metas, ListadoBase):
    template_name = "sgr/metas_lista.html"
    etiqueta_nueva = "Nueva meta"
    busqueda = ("area__nombre", "indicador__nombre", "periodo__nombre")
    relacionadas = ("periodo", "area", "indicador")
    exportar_nombre = "metas_indicador"
    exportar_columnas = (
        ("Período", "periodo.nombre"),
        ("Área", "area.nombre"),
        ("Indicador", "indicador.nombre"),
        ("Ponderador", "ponderador"),
        ("Meta", "meta"),
    )
    url_nueva = "sgr:metas_nueva"


class MetasAlta(_Metas, AltaBase):
    titulo = "Nueva meta"


class MetasEdicion(_Metas, EdicionBase):
    titulo = "Editar meta"


class MetasBorrado(_Metas, BorradoBase):
    titulo = "Eliminar meta"


class MetasDesactivar(_Metas, DesactivarBase):
    pass


class MetasReactivar(_Metas, ReactivarBase):
    pass


class MetasConsulta(_Metas, ConsultaBase):
    consulta_campos = (
        ("Período", "periodo.nombre"),
        ("Área", "area.nombre"),
        ("Indicador", "indicador.nombre"),
        ("Ponderador", "ponderador"),
        ("Meta", "meta"),
    )


# --------------------------------------------------------- Registros diarios
class _Registros:
    model = RegistroGestion
    form_class = RegistroGestionForm
    titulo = "Registros de gestión"
    seccion = "sgr_registros"
    url_listado = "sgr:registros"


class RegistrosListado(_Registros, ListadoBase):
    template_name = "sgr/registros_lista.html"
    etiqueta_nueva = "Nuevo registro"
    busqueda = ("referencia", "detalle", "area__nombre", "indicador__nombre")
    relacionadas = ("area", "indicador", "vecino", "funcionario")
    exportar_nombre = "registros_sgr"
    exportar_columnas = (
        ("Código", "referencia"),
        ("Fecha", "fecha"),
        ("Área", "area.nombre"),
        ("Indicador", "indicador.nombre"),
        ("Vecino", "vecino.nombre"),
        ("Funcionario", "funcionario.get_full_name"),
        ("Cantidad", "cantidad"),
        ("Forma", "get_forma_display"),
    )
    url_nueva = "sgr:registros_nueva"


class RegistrosAlta(_Registros, AltaBase):
    titulo = "Nuevo registro"

    def form_valid(self, form):
        respuesta = super().form_valid(form)
        self._crear_evidencia(form)
        return respuesta

    def _crear_evidencia(self, form):
        """Crea la evidencia adjunta en el mismo alta (una por actividad).

        El autor es quien registra y el vínculo con la actividad es el registro
        recién creado.
        """
        archivo = form.cleaned_data.get("evidencia_archivo")
        vinculo = form.cleaned_data.get("evidencia_vinculo")
        if not (archivo or vinculo):
            return
        Evidencia.objects.create(
            registro=self.object,
            autor=self.request.user,
            archivo=archivo,
            vinculo=vinculo or "",
            tipo=form.cleaned_data.get("evidencia_tipo") or "",
            tamano=archivo.size if archivo else None,
        )


class RegistrosEdicion(_Registros, EdicionBase):
    titulo = "Editar registro"


class RegistrosBorrado(_Registros, BorradoBase):
    titulo = "Eliminar registro"


class RegistrosDesactivar(_Registros, DesactivarBase):
    pass


class RegistrosReactivar(_Registros, ReactivarBase):
    pass


class RegistrosConsulta(_Registros, ConsultaBase):
    consulta_tubo = (("actividad", "Enviar al tubo"),)
    consulta_campos = (
        ("Código", "referencia"),
        ("Fecha", "fecha"),
        ("Área", "area.nombre"),
        ("Indicador", "indicador.nombre"),
        ("Vecino", "vecino.nombre"),
        ("Funcionario", "funcionario.get_full_name"),
        ("Cantidad", "cantidad"),
        ("Actividad", "get_actividad_display"),
        ("Compromiso", "compromiso.referencia"),
        ("Acción", "accion"),
        ("Detalle", "detalle"),
    )


# ------------------------------------------------ Reclamos y felicitaciones
class _Conductas:
    model = AjusteConducta
    form_class = AjusteConductaForm
    titulo = "Reclamos y felicitaciones"
    seccion = "sgr_conductas"
    url_listado = "sgr:conductas"


class ConductasListado(_Conductas, ListadoBase):
    template_name = "sgr/conductas_lista.html"
    etiqueta_nueva = "Nuevo reclamo o felicitación"
    busqueda = ("referencia", "respaldo", "area__nombre")
    relacionadas = ("area", "periodo")
    exportar_nombre = "conductas"
    exportar_columnas = (
        ("Código", "referencia"),
        ("Área", "area.nombre"),
        ("Tipo", "get_tipo_display"),
        ("Fecha", "fecha"),
        ("Respaldo", "respaldo"),
        ("Valor", "valor"),
    )
    url_nueva = "sgr:conductas_nueva"


class ConductasAlta(_Conductas, AltaBase):
    titulo = "Nuevo reclamo o felicitación"


class ConductasEdicion(_Conductas, EdicionBase):
    titulo = "Editar reclamo o felicitación"


class ConductasBorrado(_Conductas, BorradoBase):
    titulo = "Eliminar reclamo o felicitación"


class ConductasDesactivar(_Conductas, DesactivarBase):
    pass


class ConductasReactivar(_Conductas, ReactivarBase):
    pass


class ConductasConsulta(_Conductas, ConsultaBase):
    consulta_campos = (
        ("Código", "referencia"),
        ("Área", "area.nombre"),
        ("Tipo", "get_tipo_display"),
        ("Fecha", "fecha"),
        ("Respaldo", "respaldo"),
        ("Valor", "valor"),
        ("Período", "periodo.nombre"),
    )


# ------------------------------------------------------------------ Ausencias
class _Ausencias:
    model = Ausencia
    form_class = AusenciaForm
    titulo = "Ausencias"
    seccion = "sgr_ausencias"
    url_listado = "sgr:ausencias"


class AusenciasListado(_Ausencias, ListadoBase):
    template_name = "sgr/ausencias_lista.html"
    etiqueta_nueva = "Nueva ausencia"
    busqueda = ("referencia", "area__nombre", "periodo__nombre")
    relacionadas = ("area", "periodo")
    exportar_nombre = "ausencias"
    exportar_columnas = (
        ("Código", "referencia"),
        ("Área", "area.nombre"),
        ("Período", "periodo.nombre"),
        ("Tipo", "get_tipo_display"),
        ("Desde", "desde"),
        ("Hasta", "hasta"),
        ("Días", "dias"),
    )
    url_nueva = "sgr:ausencias_nueva"


class AusenciasAlta(_Ausencias, AltaBase):
    titulo = "Nueva ausencia"


class AusenciasEdicion(_Ausencias, EdicionBase):
    titulo = "Editar ausencia"


class AusenciasBorrado(_Ausencias, BorradoBase):
    titulo = "Eliminar ausencia"


class AusenciasDesactivar(_Ausencias, DesactivarBase):
    pass


class AusenciasReactivar(_Ausencias, ReactivarBase):
    pass


class AusenciasConsulta(_Ausencias, ConsultaBase):
    consulta_campos = (
        ("Código", "referencia"),
        ("Área", "area.nombre"),
        ("Período", "periodo.nombre"),
        ("Tipo", "get_tipo_display"),
        ("Desde", "desde"),
        ("Hasta", "hasta"),
        ("Días", "dias"),
    )


# ---------------------------------------------------------------- Tablero
class Tablero(LoginRequiredMixin, PermisoRequeridoMixin, TemplateView):
    """El resumen de la Matriz: áreas, meta al día, avance y semáforo."""

    template_name = "sgr/tablero.html"
    model = Periodo
    titulo = "Tablero SGR"
    seccion = "sgr_tablero"
    url_listado = "sgr:tablero"

    def get_context_data(self, **kwargs):
        contexto = super().get_context_data(**kwargs)
        elegido = self.request.GET.get("periodo")
        periodo = (
            servicios.periodo_activo(elegido)
            if elegido
            else contexto_periodo.activa(self.request)
        )
        contexto.update(
            titulo=self.titulo,
            seccion=self.seccion,
            resumen=servicios.resumen_periodo(periodo),
            periodos=Periodo.objects.all(),
        )
        return contexto


class FichaPersonal(LoginRequiredMixin, PermisoRequeridoMixin, TemplateView):
    """La ficha de una persona (área): sus ítems, avance y semáforo (RF-028)."""

    template_name = "sgr/personal.html"
    model = Area
    titulo = "Ficha personal"
    seccion = "sgr_tablero"
    url_listado = "sgr:tablero"

    def get_context_data(self, **kwargs):
        contexto = super().get_context_data(**kwargs)
        area = get_object_or_404(
            Area.objects.select_related("cargo", "responsable", "delegacion"),
            pk=self.kwargs["pk"],
        )
        elegido = self.request.GET.get("periodo")
        periodo = (
            servicios.periodo_activo(elegido)
            if elegido
            else contexto_periodo.activa(self.request)
        )
        contexto.update(
            titulo=str(area),
            seccion=self.seccion,
            url_listado=self.url_listado,
            area=area,
            resumen=servicios.resumen_area(periodo, area),
            periodo=periodo,
            periodos=Periodo.objects.all(),
        )
        return contexto


class TableroGlobal(LoginRequiredMixin, PermisoRequeridoMixin, TemplateView):
    """El consolidado por cargo (RF-031)."""

    template_name = "sgr/global.html"
    model = Area
    titulo = "Vista global por cargos"
    seccion = "sgr_global"
    url_listado = "sgr:global"

    def get_context_data(self, **kwargs):
        contexto = super().get_context_data(**kwargs)
        elegido = self.request.GET.get("periodo")
        periodo = (
            servicios.periodo_activo(elegido)
            if elegido
            else contexto_periodo.activa(self.request)
        )
        contexto.update(
            titulo=self.titulo,
            seccion=self.seccion,
            url_listado=self.url_listado,
            filas=servicios.resumen_por_cargo(periodo),
            periodo=periodo,
            periodos=Periodo.objects.all(),
        )
        return contexto


# --------------------------------------------------------------- Evidencias
class _Evidencias:
    model = Evidencia
    form_class = EvidenciaForm
    titulo = "Evidencias"
    seccion = "sgr_evidencias"
    url_listado = "sgr:evidencias"


class EvidenciasListado(_Evidencias, ListadoBase):
    template_name = "sgr/evidencias_lista.html"
    etiqueta_nueva = "Nueva evidencia"
    busqueda = ("referencia", "tipo", "registro__referencia", "autor__first_name")
    relacionadas = ("registro", "autor")
    exportar_nombre = "evidencias"
    exportar_columnas = (
        ("Código", "referencia"),
        ("Registro", "registro.referencia"),
        ("Autor", "autor.get_full_name"),
        ("Revisión", "get_estado_revision_display"),
        ("Fecha", "fecha"),
    )
    url_nueva = "sgr:evidencias_nueva"


class EvidenciasAlta(_Evidencias, AltaBase):
    titulo = "Nueva evidencia"

    def form_valid(self, form):
        form.instance.autor = self.request.user
        return super().form_valid(form)


class EvidenciasEdicion(_Evidencias, EdicionBase):
    titulo = "Editar evidencia"


class EvidenciasBorrado(_Evidencias, BorradoBase):
    titulo = "Eliminar evidencia"


class EvidenciasConsulta(_Evidencias, ConsultaBase):
    consulta_campos = (
        ("Código", "referencia"),
        ("Registro", "registro.referencia"),
        ("Autor", "autor.get_full_name"),
        ("Tipo", "tipo"),
        ("Vínculo", "vinculo"),
        ("Revisión", "get_estado_revision_display"),
        ("Fecha", "fecha"),
    )


# -------------------------------------------------------------- Validaciones
class _Validaciones:
    model = Validacion
    form_class = ValidacionForm
    titulo = "Validaciones"
    seccion = "sgr_validaciones"
    url_listado = "sgr:validaciones"


class ValidacionesListado(_Validaciones, ListadoBase):
    template_name = "sgr/validaciones_lista.html"
    etiqueta_nueva = "Validar evidencia"
    busqueda = ("referencia", "evidencia__referencia", "observacion")
    relacionadas = ("evidencia", "verificador")
    exportar_nombre = "validaciones"
    exportar_columnas = (
        ("Código", "referencia"),
        ("Evidencia", "evidencia.referencia"),
        ("Verificador", "verificador.get_full_name"),
        ("Decisión", "get_decision_display"),
        ("Fecha", "fecha"),
    )
    url_nueva = "sgr:validaciones_nueva"


class ValidacionesAlta(_Validaciones, AltaBase):
    titulo = "Validar evidencia"

    def form_valid(self, form):
        form.instance.verificador = self.request.user
        return super().form_valid(form)


class ValidacionesBorrado(_Validaciones, BorradoBase):
    titulo = "Eliminar validación"


class ValidacionesConsulta(_Validaciones, ConsultaBase):
    consulta_campos = (
        ("Código", "referencia"),
        ("Evidencia", "evidencia.referencia"),
        ("Verificador", "verificador.get_full_name"),
        ("Decisión", "get_decision_display"),
        ("Observación", "observacion"),
        ("Fecha", "fecha"),
    )


# -------------------------------------------------------------- Comentarios
class _Comentarios:
    model = Comentario
    form_class = ComentarioForm
    titulo = "Comentarios"
    seccion = "sgr_comentarios"
    url_listado = "sgr:comentarios"


class ComentariosListado(_Comentarios, ListadoBase):
    template_name = "sgr/comentarios_lista.html"
    etiqueta_nueva = "Nuevo comentario"
    busqueda = ("referencia", "texto", "registro__referencia", "autor__first_name")
    relacionadas = ("registro", "autor")
    exportar_nombre = "comentarios"
    exportar_columnas = (
        ("Código", "referencia"),
        ("Registro", "registro.referencia"),
        ("Autor", "autor.get_full_name"),
        ("Fecha", "fecha"),
    )
    url_nueva = "sgr:comentarios_nueva"


class ComentariosAlta(_Comentarios, AltaBase):
    titulo = "Nuevo comentario"

    def form_valid(self, form):
        form.instance.autor = self.request.user
        return super().form_valid(form)


class ComentariosEdicion(_Comentarios, EdicionBase):
    titulo = "Editar comentario"


class ComentariosBorrado(_Comentarios, BorradoBase):
    titulo = "Eliminar comentario"


class ComentariosConsulta(_Comentarios, ConsultaBase):
    consulta_campos = (
        ("Código", "referencia"),
        ("Registro", "registro.referencia"),
        ("Autor", "autor.get_full_name"),
        ("Texto", "texto"),
        ("Fecha", "fecha"),
    )


# -------------------------------------------------------------------- Alertas
class _Alertas:
    model = Alerta
    form_class = AlertaForm
    titulo = "Alertas"
    seccion = "sgr_alertas"
    url_listado = "sgr:alertas"


class AlertasListado(_Alertas, ListadoBase):
    template_name = "sgr/alertas_lista.html"
    etiqueta_nueva = "Nueva alerta"
    busqueda = ("referencia", "mensaje", "area__nombre")
    relacionadas = ("area",)
    exportar_nombre = "alertas"
    exportar_columnas = (
        ("Código", "referencia"),
        ("Tipo", "get_tipo_display"),
        ("Severidad", "get_severidad_display"),
        ("Mensaje", "mensaje"),
        ("Resuelta", "resuelta"),
        ("Fecha", "fecha"),
    )
    url_nueva = "sgr:alertas_nueva"


class AlertasAlta(_Alertas, AltaBase):
    titulo = "Nueva alerta"


class AlertasEdicion(_Alertas, EdicionBase):
    titulo = "Editar alerta"


class AlertasBorrado(_Alertas, BorradoBase):
    titulo = "Eliminar alerta"


class AlertasConsulta(_Alertas, ConsultaBase):
    consulta_campos = (
        ("Código", "referencia"),
        ("Tipo", "get_tipo_display"),
        ("Severidad", "get_severidad_display"),
        ("Mensaje", "mensaje"),
        ("Área", "area.nombre"),
        ("Resuelta", "resuelta"),
        ("Fecha", "fecha"),
    )
