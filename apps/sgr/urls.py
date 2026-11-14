from django.urls import path

from apps.sgr import views

app_name = "sgr"

urlpatterns = [
    path("sgr/", views.Tablero.as_view(), name="tablero"),
    path("sgr/global/", views.TableroGlobal.as_view(), name="global"),
    path("sgr/personal/<int:pk>/", views.FichaPersonal.as_view(), name="personal"),
    # Períodos
    path("sgr/periodos/", views.PeriodosListado.as_view(), name="periodos"),
    path("sgr/periodos/nuevo/", views.PeriodosAlta.as_view(), name="periodos_nueva"),
    path(
        "sgr/periodos/<int:pk>/",
        views.PeriodosConsulta.as_view(),
        name="periodos_consultar",
    ),
    path(
        "sgr/periodos/<int:pk>/editar/",
        views.PeriodosEdicion.as_view(),
        name="periodos_editar",
    ),
    path(
        "sgr/periodos/<int:pk>/eliminar/",
        views.PeriodosBorrado.as_view(),
        name="periodos_eliminar",
    ),
    path(
        "sgr/periodos/<int:pk>/desactivar/",
        views.PeriodosDesactivar.as_view(),
        name="periodos_desactivar",
    ),
    path(
        "sgr/periodos/<int:pk>/reactivar/",
        views.PeriodosReactivar.as_view(),
        name="periodos_reactivar",
    ),
    # Áreas
    path("sgr/areas/", views.AreasListado.as_view(), name="areas"),
    path("sgr/areas/nueva/", views.AreasAlta.as_view(), name="areas_nueva"),
    path("sgr/areas/<int:pk>/", views.AreasConsulta.as_view(), name="areas_consultar"),
    path("sgr/areas/<int:pk>/editar/", views.AreasEdicion.as_view(), name="areas_editar"),
    path("sgr/areas/<int:pk>/eliminar/", views.AreasBorrado.as_view(), name="areas_eliminar"),
    path(
        "sgr/areas/<int:pk>/desactivar/",
        views.AreasDesactivar.as_view(),
        name="areas_desactivar",
    ),
    path(
        "sgr/areas/<int:pk>/reactivar/",
        views.AreasReactivar.as_view(),
        name="areas_reactivar",
    ),
    # Indicadores
    path("sgr/indicadores/", views.IndicadoresListado.as_view(), name="indicadores"),
    path(
        "sgr/indicadores/nuevo/",
        views.IndicadoresAlta.as_view(),
        name="indicadores_nueva",
    ),
    path(
        "sgr/indicadores/<int:pk>/",
        views.IndicadoresConsulta.as_view(),
        name="indicadores_consultar",
    ),
    path(
        "sgr/indicadores/<int:pk>/editar/",
        views.IndicadoresEdicion.as_view(),
        name="indicadores_editar",
    ),
    path(
        "sgr/indicadores/<int:pk>/eliminar/",
        views.IndicadoresBorrado.as_view(),
        name="indicadores_eliminar",
    ),
    path(
        "sgr/indicadores/<int:pk>/desactivar/",
        views.IndicadoresDesactivar.as_view(),
        name="indicadores_desactivar",
    ),
    path(
        "sgr/indicadores/<int:pk>/reactivar/",
        views.IndicadoresReactivar.as_view(),
        name="indicadores_reactivar",
    ),
    # Metas
    path("sgr/metas/", views.MetasListado.as_view(), name="metas"),
    path("sgr/metas/nueva/", views.MetasAlta.as_view(), name="metas_nueva"),
    path("sgr/metas/<int:pk>/", views.MetasConsulta.as_view(), name="metas_consultar"),
    path("sgr/metas/<int:pk>/editar/", views.MetasEdicion.as_view(), name="metas_editar"),
    path("sgr/metas/<int:pk>/eliminar/", views.MetasBorrado.as_view(), name="metas_eliminar"),
    path(
        "sgr/metas/<int:pk>/desactivar/",
        views.MetasDesactivar.as_view(),
        name="metas_desactivar",
    ),
    path(
        "sgr/metas/<int:pk>/reactivar/",
        views.MetasReactivar.as_view(),
        name="metas_reactivar",
    ),
    # Registros
    path("sgr/registros/", views.RegistrosListado.as_view(), name="registros"),
    path("sgr/registros/nuevo/", views.RegistrosAlta.as_view(), name="registros_nueva"),
    path(
        "sgr/registros/<int:pk>/",
        views.RegistrosConsulta.as_view(),
        name="registros_consultar",
    ),
    path(
        "sgr/registros/<int:pk>/editar/",
        views.RegistrosEdicion.as_view(),
        name="registros_editar",
    ),
    path(
        "sgr/registros/<int:pk>/eliminar/",
        views.RegistrosBorrado.as_view(),
        name="registros_eliminar",
    ),
    path(
        "sgr/registros/<int:pk>/desactivar/",
        views.RegistrosDesactivar.as_view(),
        name="registros_desactivar",
    ),
    path(
        "sgr/registros/<int:pk>/reactivar/",
        views.RegistrosReactivar.as_view(),
        name="registros_reactivar",
    ),
    # Reclamos y felicitaciones
    path("sgr/conductas/", views.ConductasListado.as_view(), name="conductas"),
    path("sgr/conductas/nueva/", views.ConductasAlta.as_view(), name="conductas_nueva"),
    path(
        "sgr/conductas/<int:pk>/",
        views.ConductasConsulta.as_view(),
        name="conductas_consultar",
    ),
    path(
        "sgr/conductas/<int:pk>/editar/",
        views.ConductasEdicion.as_view(),
        name="conductas_editar",
    ),
    path(
        "sgr/conductas/<int:pk>/eliminar/",
        views.ConductasBorrado.as_view(),
        name="conductas_eliminar",
    ),
    path(
        "sgr/conductas/<int:pk>/desactivar/",
        views.ConductasDesactivar.as_view(),
        name="conductas_desactivar",
    ),
    path(
        "sgr/conductas/<int:pk>/reactivar/",
        views.ConductasReactivar.as_view(),
        name="conductas_reactivar",
    ),
    # Ausencias
    path("sgr/ausencias/", views.AusenciasListado.as_view(), name="ausencias"),
    path("sgr/ausencias/nueva/", views.AusenciasAlta.as_view(), name="ausencias_nueva"),
    path(
        "sgr/ausencias/<int:pk>/",
        views.AusenciasConsulta.as_view(),
        name="ausencias_consultar",
    ),
    path(
        "sgr/ausencias/<int:pk>/editar/",
        views.AusenciasEdicion.as_view(),
        name="ausencias_editar",
    ),
    path(
        "sgr/ausencias/<int:pk>/eliminar/",
        views.AusenciasBorrado.as_view(),
        name="ausencias_eliminar",
    ),
    path(
        "sgr/ausencias/<int:pk>/desactivar/",
        views.AusenciasDesactivar.as_view(),
        name="ausencias_desactivar",
    ),
    path(
        "sgr/ausencias/<int:pk>/reactivar/",
        views.AusenciasReactivar.as_view(),
        name="ausencias_reactivar",
    ),
    # Evidencias
    path("sgr/evidencias/", views.EvidenciasListado.as_view(), name="evidencias"),
    path("sgr/evidencias/nueva/", views.EvidenciasAlta.as_view(), name="evidencias_nueva"),
    path(
        "sgr/evidencias/<int:pk>/",
        views.EvidenciasConsulta.as_view(),
        name="evidencias_consultar",
    ),
    path(
        "sgr/evidencias/<int:pk>/editar/",
        views.EvidenciasEdicion.as_view(),
        name="evidencias_editar",
    ),
    path(
        "sgr/evidencias/<int:pk>/eliminar/",
        views.EvidenciasBorrado.as_view(),
        name="evidencias_eliminar",
    ),
    # Validaciones
    path("sgr/validaciones/", views.ValidacionesListado.as_view(), name="validaciones"),
    path(
        "sgr/validaciones/nueva/",
        views.ValidacionesAlta.as_view(),
        name="validaciones_nueva",
    ),
    path(
        "sgr/validaciones/<int:pk>/",
        views.ValidacionesConsulta.as_view(),
        name="validaciones_consultar",
    ),
    path(
        "sgr/validaciones/<int:pk>/eliminar/",
        views.ValidacionesBorrado.as_view(),
        name="validaciones_eliminar",
    ),
    # Comentarios
    path("sgr/comentarios/", views.ComentariosListado.as_view(), name="comentarios"),
    path("sgr/comentarios/nuevo/", views.ComentariosAlta.as_view(), name="comentarios_nueva"),
    path(
        "sgr/comentarios/<int:pk>/",
        views.ComentariosConsulta.as_view(),
        name="comentarios_consultar",
    ),
    path(
        "sgr/comentarios/<int:pk>/editar/",
        views.ComentariosEdicion.as_view(),
        name="comentarios_editar",
    ),
    path(
        "sgr/comentarios/<int:pk>/eliminar/",
        views.ComentariosBorrado.as_view(),
        name="comentarios_eliminar",
    ),
    # Alertas
    path("sgr/alertas/", views.AlertasListado.as_view(), name="alertas"),
    path("sgr/alertas/nueva/", views.AlertasAlta.as_view(), name="alertas_nueva"),
    path("sgr/alertas/<int:pk>/", views.AlertasConsulta.as_view(), name="alertas_consultar"),
    path("sgr/alertas/<int:pk>/editar/", views.AlertasEdicion.as_view(), name="alertas_editar"),
    path("sgr/alertas/<int:pk>/eliminar/", views.AlertasBorrado.as_view(), name="alertas_eliminar"),
]
