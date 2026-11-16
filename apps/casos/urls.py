from django.urls import path

from apps.casos import views

app_name = "casos"

urlpatterns = [
    path("casos/", views.CasosListado.as_view(), name="casos"),
    path("casos/nuevo/", views.CasosAlta.as_view(), name="casos_nueva"),
    path("casos/<int:pk>/", views.CasosConsulta.as_view(), name="casos_consultar"),
    path("casos/<int:pk>/editar/", views.CasosEdicion.as_view(), name="casos_editar"),
    path("casos/<int:pk>/eliminar/", views.CasosBorrado.as_view(), name="casos_eliminar"),
    path(
        "casos/<int:pk>/desactivar/",
        views.CasosDesactivar.as_view(),
        name="casos_desactivar",
    ),
    path(
        "casos/<int:pk>/reactivar/",
        views.CasosReactivar.as_view(),
        name="casos_reactivar",
    ),
    path("casos/llamadas/", views.LlamadasListado.as_view(), name="llamadas"),
    path("casos/llamadas/nueva/", views.LlamadasAlta.as_view(), name="llamadas_nueva"),
    path(
        "casos/llamadas/<int:pk>/",
        views.LlamadasConsulta.as_view(),
        name="llamadas_consultar",
    ),
    path(
        "casos/llamadas/<int:pk>/editar/",
        views.LlamadasEdicion.as_view(),
        name="llamadas_editar",
    ),
    path(
        "casos/llamadas/<int:pk>/cerrar/",
        views.LlamadasCerrar.as_view(),
        name="llamadas_cerrar",
    ),
]
