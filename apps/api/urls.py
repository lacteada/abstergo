"""Rutas de la API `v1`."""

from django.urls import include, path
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from . import views

router = DefaultRouter()
router.register("roles", views.RolViewSet)
router.register("usuarios", views.UsuarioViewSet)
router.register("delegaciones", views.DelegacionViewSet)
router.register("metas", views.MetaViewSet)
router.register("tipos-atencion", views.TipoAtencionViewSet)
router.register("sub-atenciones", views.SubAtencionViewSet)
router.register("vecinos", views.VecinoViewSet)
router.register("atenciones", views.AtencionViewSet)

urlpatterns = [
    path("auth/login/", TokenObtainPairView.as_view(), name="api-login"),
    path("auth/refresh/", TokenRefreshView.as_view(), name="api-refresh"),
    path("auth/logout/", views.LogoutView.as_view(), name="api-logout"),
    path("auth/me/", views.MeView.as_view(), name="api-me"),
    path("auth/recuperar/", views.RecuperarPasswordView.as_view(), name="api-recuperar"),
    path("auth/validar/", views.ValidarCodigoView.as_view(), name="api-validar"),
    path(
        "auth/nueva-password/",
        views.NuevaPasswordView.as_view(),
        name="api-nueva-password",
    ),
    path("", include(router.urls)),
]
