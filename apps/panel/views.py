from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse
from django.utils import timezone
from django.views.generic import TemplateView

from apps.atenciones.models import Atencion
from apps.ciudadanos.models import Vecino
from apps.common.permisos import codigo_de, modulos_de
from apps.organizacion.models import Delegacion

# (título, nombre de ruta, descripción, módulo, requiere escritura)
CATALOGO_ACCIONES = [
    ("Crear Atención", "atenciones:crear", "Registrar la atención de un vecino.", "atenciones", True),
    ("Atenciones", "atenciones:listado", "Revisar las atenciones registradas.", "atenciones", False),
    ("Vecinos", "ciudadanos:vecinos", "Mantenedor de vecinos.", "vecinos", False),
    ("Delegaciones", "organizacion:delegaciones", "Mantenedor de delegaciones.", "delegaciones", False),
    ("Usuarios", "cuentas:usuarios", "Mantenedor de usuarios.", "usuarios", False),
    ("Roles", "cuentas:roles", "Mantenedor de roles.", "roles", False),
    ("Metas", "catalogos:metas", "Metas por delegación.", "metas", False),
    ("Tipos de atención", "catalogos:tipos", "Catálogo de tipos de atención.", "tipos", False),
    ("Sub atenciones", "catalogos:subatenciones", "Catálogo de sub atenciones.", "subatenciones", False),
]


def acciones_del_rol(usuario):
    """Las acciones del dashboard que el rol puede hacer, según la matriz."""
    lectura = modulos_de(usuario)
    escritura = modulos_de(usuario, escritura=True)
    return [
        {"titulo": titulo, "url": reverse(nombre), "descripcion": descripcion}
        for titulo, nombre, descripcion, modulo, requiere_escritura in CATALOGO_ACCIONES
        if modulo in (escritura if requiere_escritura else lectura)
    ]


class Inicio(LoginRequiredMixin, TemplateView):
    template_name = "inicio.html"

    def get_context_data(self, **kwargs):
        contexto = super().get_context_data(**kwargs)
        usuario = self.request.user
        codigo = codigo_de(usuario)
        contexto["seccion"] = "inicio"
        contexto["codigo_rol"] = codigo
        contexto["acciones"] = acciones_del_rol(usuario)

        atenciones = Atencion.objects.all()
        if codigo in ("funcionario", "delegado") and usuario.delegacion_id:
            atenciones = atenciones.filter(delegacion_id=usuario.delegacion_id)
        contexto["total_atenciones"] = atenciones.count()
        contexto["atenciones_hoy"] = atenciones.filter(
            fecha__date=timezone.localdate()
        ).count()
        contexto["total_vecinos"] = Vecino.objects.count()
        contexto["total_delegaciones"] = Delegacion.objects.count()
        if codigo == "funcionario":
            contexto["mis_atenciones"] = Atencion.objects.filter(
                funcionario=usuario
            ).count()
        return contexto
