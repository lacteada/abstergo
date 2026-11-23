from django.urls import path

from apps.tubo import views

app_name = "tubo"

urlpatterns = [
    path("tubo/", views.Tablero.as_view(), name="tablero"),
    path("tubo/tareas/", views.Listado.as_view(), name="tareas"),
    path("tubo/tareas/nueva/", views.Alta.as_view(), name="tareas_nueva"),
    path("tubo/tareas/<int:pk>/", views.Consulta.as_view(), name="tareas_consultar"),
    path("tubo/tareas/<int:pk>/editar/", views.Edicion.as_view(), name="tareas_editar"),
    path("tubo/tareas/<int:pk>/eliminar/", views.Borrado.as_view(), name="tareas_eliminar"),
    path("tubo/tareas/<int:pk>/desactivar/", views.Desactivar.as_view(), name="tareas_desactivar"),
    path("tubo/tareas/<int:pk>/reactivar/", views.Reactivar.as_view(), name="tareas_reactivar"),
    path("tubo/tareas/<int:pk>/mover/", views.Mover.as_view(), name="tareas_mover"),
    path("tubo/enviar/<str:origen>/<int:pk>/", views.EnviarAlTubo.as_view(), name="enviar"),
    path("tubo/tareas/<int:pk>/reasignar/", views.Reasignar.as_view(), name="tareas_reasignar"),
    path(
        "tubo/tareas/<int:pk>/historial/",
        views.Historial.as_view(),
        name="tareas_historial",
    ),
    path("tubo/agenda/", views.Agenda.as_view(), name="agenda"),
    path("tubo/cartas/", views.CartasListado.as_view(), name="cartas"),
    path("tubo/cartas/kanban/", views.CartasTablero.as_view(), name="cartas_kanban"),
    path("tubo/cartas/nueva/", views.CartasAlta.as_view(), name="cartas_nueva"),
    path(
        "tubo/cartas/<int:pk>/",
        views.CartasConsulta.as_view(),
        name="cartas_consultar",
    ),
    path(
        "tubo/cartas/<int:pk>/editar/",
        views.CartasEdicion.as_view(),
        name="cartas_editar",
    ),
    path(
        "tubo/cartas/<int:pk>/mover/",
        views.CartaMover.as_view(),
        name="cartas_mover",
    ),
    path(
        "tubo/cartas/<int:pk>/eliminar/",
        views.CartasBorrado.as_view(),
        name="cartas_eliminar",
    ),
    path(
        "tubo/cartas/<int:pk>/desactivar/",
        views.CartasDesactivar.as_view(),
        name="cartas_desactivar",
    ),
    path(
        "tubo/cartas/<int:pk>/reactivar/",
        views.CartasReactivar.as_view(),
        name="cartas_reactivar",
    ),
]
