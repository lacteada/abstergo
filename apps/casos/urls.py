from django.urls import path

from apps.casos import views

app_name = "casos"

urlpatterns = [
    # Casos
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
    # Gestiones
    path("gestiones/", views.GestionesListado.as_view(), name="gestiones"),
    path("gestiones/nueva/", views.GestionesAlta.as_view(), name="gestiones_nueva"),
    path(
        "gestiones/<int:pk>/",
        views.GestionesConsulta.as_view(),
        name="gestiones_consultar",
    ),
    path(
        "gestiones/<int:pk>/editar/",
        views.GestionesEdicion.as_view(),
        name="gestiones_editar",
    ),
    path(
        "gestiones/<int:pk>/eliminar/",
        views.GestionesBorrado.as_view(),
        name="gestiones_eliminar",
    ),
    path(
        "gestiones/<int:pk>/desactivar/",
        views.GestionesDesactivar.as_view(),
        name="gestiones_desactivar",
    ),
    path(
        "gestiones/<int:pk>/reactivar/",
        views.GestionesReactivar.as_view(),
        name="gestiones_reactivar",
    ),
    # Llamadas preventivas
    path("llamadas/", views.LlamadasListado.as_view(), name="llamadas"),
    path("llamadas/nueva/", views.LlamadasAlta.as_view(), name="llamadas_nueva"),
    path("llamadas/<int:pk>/", views.LlamadasConsulta.as_view(), name="llamadas_consultar"),
    path("llamadas/<int:pk>/editar/", views.LlamadasEdicion.as_view(), name="llamadas_editar"),
    path("llamadas/<int:pk>/eliminar/", views.LlamadasBorrado.as_view(), name="llamadas_eliminar"),
    path(
        "llamadas/<int:pk>/desactivar/",
        views.LlamadasDesactivar.as_view(),
        name="llamadas_desactivar",
    ),
    path(
        "llamadas/<int:pk>/reactivar/",
        views.LlamadasReactivar.as_view(),
        name="llamadas_reactivar",
    ),
]
