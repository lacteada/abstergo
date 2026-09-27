from django.urls import path

from apps.ciudadanos import views

app_name = "ciudadanos"

urlpatterns = [
    path("vecinos/", views.Listado.as_view(), name="vecinos"),
    path("vecinos/nuevo/", views.Alta.as_view(), name="vecinos_nueva"),
    path("vecinos/<int:pk>/editar/", views.Edicion.as_view(), name="vecinos_editar"),
    path("vecinos/<int:pk>/eliminar/", views.Borrado.as_view(), name="vecinos_eliminar"),
]
