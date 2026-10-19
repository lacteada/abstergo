"""Carga los JSON de datos_nuevos/ en la base de datos usando el ORM.

Es reejecutable: usa update_or_create, así que correrlo dos veces deja los
mismos conteos.
"""

import json
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand
from django.db import transaction

from apps.catalogos.models import Meta, SubAtencion, TipoAtencion
from apps.ciudadanos.models import Vecino
from apps.common.validators import normalizar_rut
from apps.cuentas.models import Rol, Usuario
from apps.organizacion.models import Delegacion

DATOS = Path(settings.BASE_DIR) / "datos_nuevos"


def leer(nombre):
    with (DATOS / f"{nombre}.json").open(encoding="utf-8") as archivo:
        return json.load(archivo)


class Command(BaseCommand):
    help = "Carga datos_nuevos/ en la base de datos. Reejecutable sin duplicar."

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.creados = 0
        self.actualizados = 0

    def anotar(self, creado):
        if creado:
            self.creados += 1
        else:
            self.actualizados += 1

    def cargar(self, archivo, modelo, clave, armar):
        """Recorre un archivo y escribe con update_or_create.

        Las entidades tienen borrado lógico, así que usa el gestor sin filtro
        (`todos`) y limpia `eliminado`: recargar el JSON restaura lo dado de
        baja en vez de chocar contra el campo único.
        """
        for fila in leer(archivo):
            valores = armar(fila)
            valores["eliminado"] = None
            _, creado = modelo.todos.update_or_create(
                **{clave: fila[clave]},
                defaults=valores,
            )
            self.anotar(creado)

    @transaction.atomic
    def handle(self, *args, **options):
        self.cargar(
            "delegaciones",
            Delegacion,
            "codigo",
            lambda f: {
                "nombre": f["nombre"],
                "direccion": f["direccion"],
                "comuna": f["comuna"],
                "estado": f.get("estado", "activo"),
            },
        )
        self.cargar(
            "roles",
            Rol,
            "codigo",
            lambda f: {"nombre": f["nombre"], "descripcion": f["descripcion"]},
        )
        self.cargar_usuarios()
        self.cargar(
            "metas",
            Meta,
            "codigo",
            lambda f: {
                "nombre": f["nombre"],
                "descripcion": f["descripcion"],
                "delegacion": Delegacion.objects.get(codigo=f["delegacion"]),
                "estado": f.get("estado", "activo"),
            },
        )
        self.cargar(
            "tipos_atencion",
            TipoAtencion,
            "codigo",
            lambda f: {
                "nombre": f["nombre"],
                "descripcion": f["descripcion"],
                "estado": f.get("estado", "activo"),
            },
        )
        self.cargar(
            "sub_atenciones",
            SubAtencion,
            "codigo",
            lambda f: {
                "nombre": f["nombre"],
                "tipo_atencion": TipoAtencion.objects.get(nombre=f["tipo_atencion"]),
                "estado": f.get("estado", "activo"),
            },
        )
        self.cargar(
            "vecinos",
            Vecino,
            "rut",
            lambda f: {
                "nombre": f["nombre"],
                "rut": normalizar_rut(f["rut"]),
                "direccion": f["direccion"],
                "telefono": f["telefono"],
                "territorio": Delegacion.objects.get(codigo=f["territorio"]),
                "tipo_gestion": f["tipo_gestion"],
                "estado": f["estado"],
            },
        )
        self.stdout.write(
            self.style.SUCCESS(
                f"Listo: {self.creados} creados, {self.actualizados} actualizados."
            )
        )

    def cargar_usuarios(self):
        """El rol y la delegación van en el propio usuario.

        La llave de idempotencia es el nombre completo, no el correo: un
        usuario sin correo lo tiene nulo y no sirve para buscar. Sin correo la
        contraseña queda inutilizable, porque ese usuario no puede entrar.

        `superusuario` en el JSON da acceso al Django Admin (tablas de la ley);
        sin la bandera, el usuario es solo de la aplicación.
        """
        for fila in leer("usuarios"):
            nombre, _, apellido = fila["nombre"].partition(" ")
            correo = fila.get("email") or None
            superusuario = bool(fila.get("superusuario", False))
            usuario, creado = Usuario.objects.update_or_create(
                first_name=nombre,
                last_name=apellido,
                defaults={
                    "email": correo,
                    "rol": Rol.objects.get(nombre=fila["rol"]),
                    "delegacion": Delegacion.objects.get(codigo=fila["delegacion"]),
                    "is_active": fila["activo"],
                    "is_staff": superusuario,
                    "is_superuser": superusuario,
                    "eliminado": None,
                },
            )
            if creado:
                usuario.set_password(
                    settings.USUARIOS_PASSWORD_INICIAL if correo else None
                )
                usuario.save()
            # La semilla manda: se fija la lista completa de autorizadas, así
            # reejecutar deja el contexto igual y no arrastra una lista vieja.
            usuario.delegaciones_autorizadas.set(
                Delegacion.objects.filter(codigo__in=fila.get("delegaciones") or [])
            )
            self.anotar(creado)
