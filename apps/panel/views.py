from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse
from django.utils import timezone
from django.views.generic import TemplateView

from apps.atenciones.models import Atencion
from apps.ciudadanos.models import Vecino
from apps.organizacion.models import Delegacion


CATALOGO_ACCIONES = [
    ("Crear Atención", "atenciones:crear", "Registrar la atención de un vecino."),
    ("Atenciones", "atenciones:listado", "Revisar las atenciones registradas."),
    ("Vecinos", "ciudadanos:vecinos", "Mantenedor de vecinos."),
    ("Delegaciones", "organizacion:delegaciones", "Mantenedor de delegaciones."),
    ("Usuarios", "cuentas:usuarios", "Mantenedor de usuarios."),
    ("Roles", "cuentas:roles", "Mantenedor de roles."),
    ("Metas", "catalogos:metas", "Metas por delegación."),
    ("Tipos de atención", "catalogos:tipos", "Catálogo de tipos de atención."),
    ("Sub atenciones", "catalogos:subatenciones", "Catálogo de sub atenciones."),
]

# Qué acciones ve cada rol en el dashboard. Se ramifica por `rol.codigo`, que
# es estable, y nunca por el nombre.
ACCIONES_POR_ROL = {
    "admin": [
        "Crear Atención", "Atenciones", "Vecinos", "Delegaciones", "Usuarios",
        "Roles", "Metas", "Tipos de atención", "Sub atenciones",
    ],
    "coordinador": [
        "Crear Atención", "Atenciones", "Vecinos", "Delegaciones", "Metas",
        "Tipos de atención", "Sub atenciones",
    ],
    "delegado": ["Crear Atención", "Atenciones", "Vecinos", "Metas"],
    "funcionario": ["Crear Atención", "Atenciones", "Vecinos"],
    "verificador": ["Atenciones", "Vecinos", "Tipos de atención"],
    "consulta": ["Atenciones", "Vecinos"],
}


def acciones_del_rol(codigo):
    permitidas = ACCIONES_POR_ROL.get(codigo, ["Atenciones"])
    return [
        {"titulo": titulo, "url": reverse(nombre), "descripcion": descripcion}
        for titulo, nombre, descripcion in CATALOGO_ACCIONES
        if titulo in permitidas
    ]


class Inicio(LoginRequiredMixin, TemplateView):
    template_name = "inicio.html"

    def get_context_data(self, **kwargs):
        contexto = super().get_context_data(**kwargs)
        usuario = self.request.user
        codigo = usuario.rol.codigo if usuario.rol_id else ""
        contexto["seccion"] = "inicio"
        contexto["codigo_rol"] = codigo
        contexto["acciones"] = acciones_del_rol(codigo)

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
