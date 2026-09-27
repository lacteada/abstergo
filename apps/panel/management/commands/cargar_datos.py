"""Carga los JSON de datos_nuevos/ en la base de datos usando el ORM.

Es reejecutable: usa update_or_create, así que correrlo dos veces deja los
mismos conteos.
"""

import json
from pathlib import Path

from django.conf import settings
from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from django.db import transaction

from apps.catalogos.models import Meta, SubAtencion, TipoAtencion
from apps.ciudadanos.models import Vecino
from apps.cuentas.models import PerfilUsuario, Rol
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

        En las entidades con borrado lógico se usa el gestor sin filtro, para
        que recargar el JSON restaure lo que se dio de baja en vez de chocar
        contra el campo único.
        """
        con_baja = hasattr(modelo, "eliminado")
        gestor = modelo.todos if con_baja else modelo.objects
        for fila in leer(archivo):
            valores = armar(fila)
            if con_baja:
                valores["eliminado"] = None
            _, creado = gestor.update_or_create(
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
                "activo": f["activo"],
            },
        )
        self.cargar(
            "roles",
            Rol,
            "nombre",
            lambda f: {"descripcion": f["descripcion"]},
        )
        self.cargar_usuarios()
        self.cargar(
            "metas",
            Meta,
            "nombre",
            lambda f: {"descripcion": f["descripcion"]},
        )
        self.cargar(
            "tipos_atencion",
            TipoAtencion,
            "nombre",
            lambda f: {"descripcion": f["descripcion"]},
        )
        self.cargar(
            "sub_atenciones",
            SubAtencion,
            "nombre",
            lambda f: {"tipo_atencion": TipoAtencion.objects.get(nombre=f["tipo_atencion"])},
        )
        self.cargar(
            "vecinos",
            Vecino,
            "rut",
            lambda f: {
                "nombre": f["nombre"],
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
        """Los usuarios traen rol y delegación por referencia, y contraseña del .env."""
        for fila in leer("usuarios"):
            nombre, _, apellido = fila["nombre"].partition(" ")
            usuario, creado = User.objects.update_or_create(
                username=fila["email"],
                defaults={
                    "email": fila["email"],
                    "first_name": nombre,
                    "last_name": apellido,
                },
            )
            if creado:
                usuario.set_password(settings.USUARIOS_PASSWORD_INICIAL)
                usuario.save()
            self.anotar(creado)

            PerfilUsuario.objects.update_or_create(
                usuario=usuario,
                defaults={
                    "rol": Rol.objects.get(nombre=fila["rol"]),
                    "delegacion": Delegacion.objects.get(codigo=fila["delegacion"]),
                    "estado": (
                        PerfilUsuario.ACTIVO if fila["activo"] else PerfilUsuario.INACTIVO
                    ),
                },
            )
