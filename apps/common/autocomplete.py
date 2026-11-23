"""Autocompletado de los campos de selección (llaves foráneas).

Un solo motor sirve los resultados de cualquier modelo registrado: el widget
apunta a `/autocompletar/<slug>/` y esta vista busca por los campos declarados,
respetando el alcance territorial del usuario. Así el buscador aparece en todos
los formularios del CRUD sin repetirlo campo por campo.
"""

from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q
from django.http import JsonResponse
from django.views import View

from apps.common.delegaciones import acotar, campo_delegacion_de

# slug -> (modelo, campos de búsqueda, cómo se rotula cada resultado)
REGISTRO = {}

_REGISTRADO = False


def registrar(slug, modelo, campos, etiqueta=None):
    REGISTRO[slug] = (modelo, tuple(campos), etiqueta or str)


def slug_de(modelo):
    """El slug del modelo, o None si no tiene autocompletado."""
    _asegurar_registro()
    for slug, (registrado, _, _) in REGISTRO.items():
        if registrado is modelo:
            return slug
    return None


def _vigentes(modelo):
    """El queryset a buscar: sin los dados de baja."""
    if hasattr(modelo, "vigentes"):
        return modelo.vigentes()
    return modelo.objects.all()


class Autocompletar(LoginRequiredMixin, View):
    """Devuelve los primeros resultados que calzan con `?q=`."""

    limite = 20

    def get(self, request, slug):
        _asegurar_registro()
        registro = REGISTRO.get(slug)
        if registro is None:
            return JsonResponse({"resultados": []}, status=404)
        modelo, campos, etiqueta = registro
        consulta = request.GET.get("q", "").strip()
        queryset = _vigentes(modelo)
        if consulta and campos:
            condicion = Q()
            for campo in campos:
                condicion |= Q(**{f"{campo}__icontains": consulta})
            queryset = queryset.filter(condicion)
        queryset = acotar(request, queryset, campo_delegacion_de(modelo))
        resultados = [
            {"id": objeto.pk, "text": etiqueta(objeto)}
            for objeto in queryset[: self.limite]
        ]
        return JsonResponse({"resultados": resultados})


def _registrar_modelos():
    from apps.catalogos.models import Meta, SubAtencion, TipoAtencion
    from apps.ciudadanos.models import Vecino
    from apps.comunidad.models import Organizacion
    from apps.cuentas.models import Usuario
    from apps.organizacion.models import Cargo, Delegacion, Territorio
    from apps.sgr.models import Area, Indicador, Periodo
    from apps.tubo.models import TareaTubo

    registrar("vecino", Vecino, ("nombre", "rut"), lambda o: f"{o.nombre} · {o.rut}")
    registrar(
        "territorio", Territorio, ("nombre", "codigo"),
        lambda o: f"{o.nombre} · {o.delegacion}",
    )
    registrar(
        "delegacion", Delegacion, ("codigo", "nombre"),
        lambda o: f"{o.codigo} · {o.nombre}",
    )
    registrar("cargo", Cargo, ("nombre",), lambda o: o.nombre)
    registrar(
        "usuario", Usuario, ("first_name", "last_name", "email"),
        lambda o: o.get_full_name() or o.email or f"Usuario {o.pk}",
    )
    registrar("tipo_atencion", TipoAtencion, ("nombre",), lambda o: o.nombre)
    registrar(
        "sub_atencion", SubAtencion, ("nombre",),
        lambda o: f"{o.nombre} · {o.tipo_atencion}",
    )
    registrar("meta", Meta, ("nombre",), lambda o: f"{o.nombre} · {o.delegacion}")
    registrar("area", Area, ("nombre",), lambda o: o.nombre)
    registrar("indicador", Indicador, ("nombre",), lambda o: o.nombre)
    registrar("periodo", Periodo, ("nombre",), lambda o: o.nombre)
    registrar("organizacion", Organizacion, ("nombre",), lambda o: o.nombre)
    registrar(
        "tarea", TareaTubo, ("titulo", "referencia"),
        lambda o: f"{o.referencia} · {o.titulo}",
    )


def _asegurar_registro():
    """Registra los modelos la primera vez que se usa (evita importar en carga)."""
    global _REGISTRADO
    if _REGISTRADO:
        return
    _REGISTRADO = True
    _registrar_modelos()
