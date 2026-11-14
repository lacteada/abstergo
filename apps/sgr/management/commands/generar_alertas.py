"""Genera las alertas del sistema (RF-037)."""

from django.core.management.base import BaseCommand

from apps.sgr import alertas, servicios


class Command(BaseCommand):
    help = "Genera las alertas de tareas vencidas e ítems bajo umbral."

    def add_arguments(self, parser):
        parser.add_argument("--periodo", type=int, default=None)

    def handle(self, *args, **options):
        periodo = servicios.periodo_activo(options["periodo"])
        creadas = alertas.generar_alertas(periodo)
        self.stdout.write(self.style.SUCCESS(f"Alertas creadas: {creadas}"))
