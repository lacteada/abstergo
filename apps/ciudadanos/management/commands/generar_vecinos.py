"""Genera vecinos de relleno para pruebas de volumen.

Los RUT son válidos (dígito verificador módulo 11) y únicos, y los datos salen
de un generador con semilla fija: volver a correrlo no duplica ni cambia nada
(los RUT que ya existen se saltan). No reemplaza los datos reales; es volumen
para listados, exportación y pruebas de carga.
"""

import random

from django.core.management.base import BaseCommand
from django.db import transaction

from apps.catalogos.models import TipoAtencion
from apps.ciudadanos.models import Vecino
from apps.common.validators import digito_verificador
from apps.organizacion.models import Delegacion

NOMBRES = (
    "Ana", "Manuel", "Rosa", "Pedro", "Julia", "Héctor", "Camila", "Jorge",
    "Valentina", "Sebastián", "Antonia", "Matías", "Francisca", "Diego",
    "Constanza", "Ignacio", "Javiera", "Cristóbal", "Martina", "Vicente",
    "Isidora", "Benjamín", "Catalina", "Tomás", "Fernanda", "Agustín",
    "Josefa", "Maximiliano", "Amanda", "Lucas", "Trinidad", "Emilio",
)
APELLIDOS = (
    "Alvarado", "Contreras", "Fuentes", "Pizarro", "González", "Muñoz",
    "Rojas", "Silva", "Morales", "Sepúlveda", "Castillo", "Vergara",
    "Riquelme", "Cortés", "Álvarez", "Tapia", "Cáceres", "Vega", "Pinto",
    "Herrera", "Cárdenas", "Flores", "Espinoza", "Bravo", "Leiva",
    "Fuentealba", "Orellana", "Zúñiga", "Navarrete", "Bustamante",
)
CALLES = (
    "Los Aromos", "Balmaceda", "Av. del Mar", "Cienfuegos", "Regimiento Coquimbo",
    "Ruta 5 Norte", "Los Clarines", "Camino a Vicuña", "Arturo Prat", "Mattmani",
    "Aldunate", "O'Higgins", "Colón", "Eduardo de la Barra", "Cordovez",
)


class Command(BaseCommand):
    help = "Genera vecinos de relleno con RUT válidos y únicos."

    def add_arguments(self, parser):
        parser.add_argument(
            "--cantidad", type=int, default=1000, help="Cuántos vecinos crear."
        )
        parser.add_argument(
            "--semilla",
            type=int,
            default=20261019,
            help="Semilla del generador: misma semilla, mismos datos.",
        )

    @transaction.atomic
    def handle(self, *args, **options):
        territorios = list(Delegacion.objects.all())
        if not territorios:
            self.stderr.write("No hay delegaciones cargadas; corre cargar_datos.")
            return
        gestiones = list(TipoAtencion.objects.values_list("nombre", flat=True))
        rng = random.Random(options["semilla"])
        cantidad = options["cantidad"]
        existentes = set(Vecino.todos.values_list("rut", flat=True))

        # Cuerpos de 8 dígitos, lejos del rango de los datos de ejemplo, y en
        # una muestra barajada para que los RUT no salgan consecutivos. La
        # muestra es exactamente la cantidad pedida, así volver a correrlo
        # encuentra todos los RUT ya creados y no agrega ninguno.
        candidatos = rng.sample(range(20_000_000, 30_000_000), cantidad)
        creados = 0
        for cuerpo in candidatos:
            rut = f"{cuerpo}-{digito_verificador(cuerpo)}"
            if rut in existentes:
                continue
            Vecino.objects.create(
                nombre=(
                    f"{rng.choice(NOMBRES)} {rng.choice(APELLIDOS)} "
                    f"{rng.choice(APELLIDOS)}"
                ),
                rut=rut,
                direccion=f"{rng.choice(CALLES)} {rng.randint(10, 4999)}",
                telefono=f"+56 9 {rng.randint(1000, 9999)} {rng.randint(1000, 9999)}",
                territorio=rng.choice(territorios),
                tipo_gestion=rng.choice(gestiones) if gestiones else "",
                estado=Vecino.ACTIVO if rng.random() < 0.85 else Vecino.INACTIVO,
            )
            existentes.add(rut)
            creados += 1

        self.stdout.write(self.style.SUCCESS(f"Listo: {creados} vecinos creados."))
