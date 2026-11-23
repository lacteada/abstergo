from django.urls import path

from apps.panel import views

app_name = "panel"

urlpatterns = [
    path("", views.Inicio.as_view(), name="inicio"),
    path("contexto/delegacion/", views.CambiarDelegacion.as_view(), name="cambiar_delegacion"),
    path("contexto/periodo/", views.CambiarPeriodo.as_view(), name="cambiar_periodo"),
]
