from django.urls import path

from apps.organizacion import views

app_name = "organizacion"

urlpatterns = [
    path("delegaciones/", views.Listado.as_view(), name="delegaciones"),
    path("delegaciones/nueva/", views.Alta.as_view(), name="delegaciones_nueva"),
    path(
        "delegaciones/<int:pk>/",
        views.Consulta.as_view(),
        name="delegaciones_consultar",
    ),
    path(
        "delegaciones/<int:pk>/editar/",
        views.Edicion.as_view(),
        name="delegaciones_editar",
    ),
    path(
        "delegaciones/<int:pk>/eliminar/",
        views.Borrado.as_view(),
        name="delegaciones_eliminar",
    ),
    path(
        "delegaciones/<int:pk>/desactivar/",
        views.Desactivar.as_view(),
        name="delegaciones_desactivar",
    ),
    path(
        "delegaciones/<int:pk>/reactivar/",
        views.Reactivar.as_view(),
        name="delegaciones_reactivar",
    ),
    # Cargos
    path("cargos/", views.CargosListado.as_view(), name="cargos"),
    path("cargos/nuevo/", views.CargosAlta.as_view(), name="cargos_nueva"),
    path("cargos/<int:pk>/", views.CargosConsulta.as_view(), name="cargos_consultar"),
    path("cargos/<int:pk>/editar/", views.CargosEdicion.as_view(), name="cargos_editar"),
    path("cargos/<int:pk>/eliminar/", views.CargosBorrado.as_view(), name="cargos_eliminar"),
    path(
        "cargos/<int:pk>/desactivar/",
        views.CargosDesactivar.as_view(),
        name="cargos_desactivar",
    ),
    path(
        "cargos/<int:pk>/reactivar/",
        views.CargosReactivar.as_view(),
        name="cargos_reactivar",
    ),
]
