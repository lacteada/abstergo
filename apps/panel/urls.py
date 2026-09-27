from django.urls import path

from apps.panel import views

app_name = "panel"

urlpatterns = [
    path("", views.Inicio.as_view(), name="inicio"),
]
