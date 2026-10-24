from django.urls import path

from apps.catalogos import views

app_name = "catalogos"

urlpatterns = [
    # Metas
    path("metas/", views.MetasListado.as_view(), name="metas"),
    path("metas/nueva/", views.MetasAlta.as_view(), name="metas_nueva"),
    path("metas/<int:pk>/", views.MetasConsulta.as_view(), name="metas_consultar"),
    path("metas/<int:pk>/editar/", views.MetasEdicion.as_view(), name="metas_editar"),
    path("metas/<int:pk>/eliminar/", views.MetasBorrado.as_view(), name="metas_eliminar"),
    path("metas/<int:pk>/desactivar/", views.MetasDesactivar.as_view(), name="metas_desactivar"),
    path("metas/<int:pk>/reactivar/", views.MetasReactivar.as_view(), name="metas_reactivar"),
    # Tipo de Atención
    path("tipos-atencion/", views.TiposListado.as_view(), name="tipos"),
    path("tipos-atencion/nuevo/", views.TiposAlta.as_view(), name="tipos_nueva"),
    path(
        "tipos-atencion/<int:pk>/",
        views.TiposConsulta.as_view(),
        name="tipos_consultar",
    ),
    path(
        "tipos-atencion/<int:pk>/editar/",
        views.TiposEdicion.as_view(),
        name="tipos_editar",
    ),
    path(
        "tipos-atencion/<int:pk>/eliminar/",
        views.TiposBorrado.as_view(),
        name="tipos_eliminar",
    ),
    path(
        "tipos-atencion/<int:pk>/desactivar/",
        views.TiposDesactivar.as_view(),
        name="tipos_desactivar",
    ),
    path(
        "tipos-atencion/<int:pk>/reactivar/",
        views.TiposReactivar.as_view(),
        name="tipos_reactivar",
    ),
    # Sub Atención
    path("sub-atenciones/", views.SubAtencionesListado.as_view(), name="subatenciones"),
    path(
        "sub-atenciones/nueva/",
        views.SubAtencionesAlta.as_view(),
        name="subatenciones_nueva",
    ),
    path(
        "sub-atenciones/<int:pk>/",
        views.SubAtencionesConsulta.as_view(),
        name="subatenciones_consultar",
    ),
    path(
        "sub-atenciones/<int:pk>/editar/",
        views.SubAtencionesEdicion.as_view(),
        name="subatenciones_editar",
    ),
    path(
        "sub-atenciones/<int:pk>/eliminar/",
        views.SubAtencionesBorrado.as_view(),
        name="subatenciones_eliminar",
    ),
    path(
        "sub-atenciones/<int:pk>/desactivar/",
        views.SubAtencionesDesactivar.as_view(),
        name="subatenciones_desactivar",
    ),
    path(
        "sub-atenciones/<int:pk>/reactivar/",
        views.SubAtencionesReactivar.as_view(),
        name="subatenciones_reactivar",
    ),
]
