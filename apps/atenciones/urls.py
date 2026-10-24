from django.urls import path

from apps.atenciones import views

app_name = "atenciones"

urlpatterns = [
    path("atenciones/", views.Listado.as_view(), name="listado"),
    path("atenciones/crear/", views.CrearAtencion.as_view(), name="crear"),
    path("atenciones/<int:pk>/", views.Consulta.as_view(), name="consultar"),
    path("atenciones/<int:pk>/editar/", views.Edicion.as_view(), name="editar"),
    path("atenciones/<int:pk>/eliminar/", views.Borrado.as_view(), name="eliminar"),
    path("atenciones/<int:pk>/desactivar/", views.Desactivar.as_view(), name="desactivar"),
    path("atenciones/<int:pk>/reactivar/", views.Reactivar.as_view(), name="reactivar"),
]
