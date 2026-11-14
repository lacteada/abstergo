from django.urls import path

from apps.comunidad import views

app_name = "comunidad"

urlpatterns = [
    path("organizaciones/", views.Listado.as_view(), name="organizaciones"),
    path(
        "organizaciones/nueva/",
        views.Alta.as_view(),
        name="organizaciones_nueva",
    ),
    path(
        "organizaciones/<int:pk>/",
        views.Consulta.as_view(),
        name="organizaciones_consultar",
    ),
    path(
        "organizaciones/<int:pk>/editar/",
        views.Edicion.as_view(),
        name="organizaciones_editar",
    ),
    path(
        "organizaciones/<int:pk>/eliminar/",
        views.Borrado.as_view(),
        name="organizaciones_eliminar",
    ),
    path(
        "organizaciones/<int:pk>/desactivar/",
        views.Desactivar.as_view(),
        name="organizaciones_desactivar",
    ),
    path(
        "organizaciones/<int:pk>/reactivar/",
        views.Reactivar.as_view(),
        name="organizaciones_reactivar",
    ),
]
