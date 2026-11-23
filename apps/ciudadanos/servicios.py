"""Operaciones sobre vecinos que comparten varias apps.

Vive fuera de las vistas para que la búsqueda por nombre o RUT y la creación
desde otro formulario (por ejemplo, la directiva de una organización) tengan una
sola implementación.
"""

from django.core.exceptions import ValidationError
from django.db.models import Q

from apps.ciudadanos.models import Vecino
from apps.common.delegaciones import acotar, campo_delegacion_de
from apps.common.validators import limpiar_rut, normalizar_rut, validar_nombre, validar_rut


def vecinos_autorizados(request):
    """Los vecinos dentro del alcance territorial del usuario.

    Se usa en todo el flujo de Crear Atención (buscar, precargar, asociar) para
    que un perfil acotado no vea ni asocie vecinos de otra delegación.
    """
    return acotar(request, Vecino.objects.all(), campo_delegacion_de(Vecino))


def buscar_vecinos(consulta, request=None):
    """Un solo campo: busca por RUT (normalizado) o por nombre y apellido."""
    consulta = (consulta or "").strip()
    if not consulta:
        return Vecino.objects.none()
    vecinos = vecinos_autorizados(request) if request else Vecino.objects.all()
    return vecinos.filter(
        Q(nombre__icontains=consulta) | Q(rut__icontains=limpiar_rut(consulta))
    ).distinct()


def crear_vecino(nombre, rut, territorio):
    """Crea un vecino con su RUT normalizado y validado.

    Se usa cuando alguien (por ejemplo, un dirigente de una organización) se
    registra en el mismo formulario en que se lo necesita. Valida el RUT y el
    nombre con las mismas reglas del mantenedor y avisa si el RUT ya existe.
    """
    rut = normalizar_rut(rut)
    validar_nombre(nombre)
    validar_rut(rut)
    if Vecino.todos.filter(rut=rut).exists():
        raise ValidationError("Ya existe un vecino con ese RUT.")
    vecino = Vecino(nombre=nombre, rut=rut, territorio=territorio)
    vecino.save()
    return vecino
