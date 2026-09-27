from django.urls import path

from apps.organizacion import views

app_name = "organizacion"

urlpatterns = [
    path("delegaciones/", views.Listado.as_view(), name="delegaciones"),
    path("delegaciones/nueva/", views.Alta.as_view(), name="delegaciones_nueva"),
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
]
