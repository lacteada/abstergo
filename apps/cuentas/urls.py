from django.contrib.auth import views as auth_views
from django.urls import path

from apps.cuentas import views
from apps.cuentas.forms import FormularioLogin

app_name = "cuentas"

urlpatterns = [
    # Autenticación
    path(
        "login/",
        auth_views.LoginView.as_view(
            template_name="cuentas/login.html",
            authentication_form=FormularioLogin,
        ),
        name="login",
    ),
    path("logout/", auth_views.LogoutView.as_view(), name="logout"),
    path("recuperar/", views.Recuperar.as_view(), name="recuperar"),
    path("validar/", views.Validar.as_view(), name="validar"),
    path("reenviar/", views.Reenviar.as_view(), name="reenviar"),
    path("nueva-password/", views.NuevaPassword.as_view(), name="nueva_password"),
    # Roles
    path("roles/", views.RolesListado.as_view(), name="roles"),
    path("roles/nuevo/", views.RolesAlta.as_view(), name="roles_nueva"),
    path("roles/<int:pk>/editar/", views.RolesEdicion.as_view(), name="roles_editar"),
    path("roles/<int:pk>/eliminar/", views.RolesBorrado.as_view(), name="roles_eliminar"),
    # Usuarios
    path("usuarios/", views.UsuariosListado.as_view(), name="usuarios"),
    path("usuarios/nuevo/", views.UsuariosAlta.as_view(), name="usuarios_nueva"),
    path(
        "usuarios/<int:pk>/editar/",
        views.UsuariosEdicion.as_view(),
        name="usuarios_editar",
    ),
    path(
        "usuarios/<int:pk>/eliminar/",
        views.UsuariosBorrado.as_view(),
        name="usuarios_eliminar",
    ),
]
