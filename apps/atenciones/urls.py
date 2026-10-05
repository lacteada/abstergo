from django.urls import path

from apps.atenciones import views

app_name = "atenciones"

urlpatterns = [
    path("atenciones/", views.Listado.as_view(), name="listado"),
    path("atenciones/crear/", views.CrearAtencion.as_view(), name="crear"),
    path("atenciones/<int:pk>/editar/", views.Edicion.as_view(), name="editar"),
    path("atenciones/<int:pk>/eliminar/", views.Borrado.as_view(), name="eliminar"),
]
