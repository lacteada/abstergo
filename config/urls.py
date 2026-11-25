"""
URL configuration for config project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import include, path
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

from apps.common.autocomplete import Autocompletar
from apps.panel.calidad import Calidad

urlpatterns = [
    path("calidad/", Calidad.as_view(), name="calidad"),
    path("admin/", admin.site.urls),
    path("api/v1/", include("apps.api.urls")),
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path(
        "api/docs/",
        SpectacularSwaggerView.as_view(url_name="schema"),
        name="docs",
    ),
    path("autocompletar/<slug:slug>/", Autocompletar.as_view(), name="autocompletar"),
    path("", include("apps.cuentas.urls")),
    path("", include("apps.panel.urls")),
    path("", include("apps.organizacion.urls")),
    path("", include("apps.catalogos.urls")),
    path("", include("apps.ciudadanos.urls")),
    path("", include("apps.atenciones.urls")),
    path("", include("apps.comunidad.urls")),
    path("", include("apps.sgr.urls")),
    path("", include("apps.tubo.urls")),
    path("", include("apps.casos.urls")),
]
