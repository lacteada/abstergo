"""Rutas de la API `v1`."""

from django.urls import include, path
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from . import views

router = DefaultRouter()
router.register("roles", views.RolViewSet)
router.register("positions", views.CargoViewSet)
router.register("users", views.UsuarioViewSet)
router.register("delegations", views.DelegacionViewSet)
router.register("territories", views.TerritorioViewSet)
router.register("goals", views.MetaViewSet)
router.register("attention-types", views.TipoAtencionViewSet)
router.register("attention-subtypes", views.SubAtencionViewSet)
router.register("neighbors", views.VecinoViewSet)
router.register("cases", views.AtencionViewSet)
router.register("community-organizations", views.OrganizacionViewSet)
router.register("sgr-periods", views.PeriodoViewSet)
router.register("sgr-areas", views.AreaViewSet)
router.register("sgr-indicators", views.IndicadorViewSet)
router.register("sgr-targets", views.MetaIndicadorViewSet)
router.register("sgr-records", views.RegistroGestionViewSet)
router.register("sgr-conducts", views.AjusteConductaViewSet)
router.register("sgr-absences", views.AusenciaViewSet)
router.register("tasks", views.TareaTuboViewSet)
router.register("social-cases", views.CasoSocialViewSet)
router.register("comments", views.ComentarioViewSet)
router.register("alerts", views.AlertaViewSet)
router.register("evidence", views.EvidenciaViewSet)
router.register("validations", views.ValidacionViewSet)

urlpatterns = [
    path("auth/login/", TokenObtainPairView.as_view(), name="api-login"),
    path("auth/refresh/", TokenRefreshView.as_view(), name="api-refresh"),
    path("auth/logout/", views.LogoutView.as_view(), name="api-logout"),
    path("auth/me/", views.MeView.as_view(), name="api-me"),
    path("auth/recover/", views.RecuperarPasswordView.as_view(), name="api-recover"),
    path("auth/register/", views.RegistroView.as_view(), name="api-register"),
    path("auth/verify/", views.ValidarCodigoView.as_view(), name="api-verify"),
    path(
        "auth/new-password/",
        views.NuevaPasswordView.as_view(),
        name="api-new-password",
    ),
    path("", include(router.urls)),
]
