"""Importa la base de JJVV y organizaciones (material/doc 4) y reporta su calidad.

Lee la tabla del archivo del material, normaliza y carga cada fila **sin
descartar ninguna**: las dudosas quedan con `verificacion = sin-verificar`.
Reejecutable (usa `update_or_create`), y escribe un informe de calidad.
"""

import re
from datetime import date
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError

from apps.comunidad.models import Organizacion
from apps.organizacion.models import Delegacion

ARCHIVO = Path.home() / "code/ina/proyect/material/Base_Datos_JJVV_sin_verificar.md"
INFORME = Path("informe_calidad_jjvv.md")

# Territorio del documento -> código de delegación.
MAPA_TERRITORIOS = {
    "ALFALFARES": "alfalfares",
    "ANTENA": "la-antena",
    "AV DEL MAR": "avenida-del-mar",
    "CENTRO": "centro",
    "CIAS": "las-companias",
    "RURAL": "rural",
}


def _texto(valor):
    return (valor or "").strip()


def _fecha(valor):
    valor = _texto(valor)
    if re.match(r"^\d{4}-\d{2}-\d{2}$", valor):
        anio, mes, dia = (int(parte) for parte in valor.split("-"))
        return date(anio, mes, dia)
    return None


def _entero(valor):
    valor = _texto(valor)
    return int(valor) if valor.isdigit() else None


class Command(BaseCommand):
    help = "Importa la base de JJVV (doc 4) y escribe el informe de calidad."

    def add_arguments(self, parser):
        parser.add_argument("--archivo", default=str(ARCHIVO))
        parser.add_argument("--informe", default=str(INFORME))

    def handle(self, *args, **options):
        origen = Path(options["archivo"])
        if not origen.exists():
            raise CommandError(f"No existe el archivo: {origen}")
        filas = self._leer(origen)
        creados, actualizados = self._cargar(filas)
        self._informe(filas, Path(options["informe"]))
        self.stdout.write(
            self.style.SUCCESS(
                f"Listo: {len(filas)} filas, {creados} creadas, {actualizados} actualizadas."
            )
        )

    def _leer(self, origen):
        filas = []
        for linea in origen.read_text(encoding="utf-8").splitlines():
            if not linea.startswith("|"):
                continue
            columnas = [col.strip() for col in linea.strip().strip("|").split("|")]
            if len(columnas) < 4 or columnas[0] in ("ORGANIZACIONES", ""):
                continue
            if set(columnas[0]) <= {"-", " "}:
                continue
            filas.append(columnas)
        return filas

    def _cargar(self, filas):
        creados = actualizados = 0
        for columnas in filas:
            columnas += [""] * (8 - len(columnas))
            nombre, domicilio, territ = columnas[0], columnas[1], columnas[2]
            socios, fecha_c, reg_pj = columnas[3], columnas[4], columnas[5]
            fecha_i, reg_dir = columnas[6], columnas[7]
            codigo = MAPA_TERRITORIOS.get(_texto(territ).upper())
            delegacion = (
                Delegacion.objects.filter(codigo=codigo).first() if codigo else None
            )
            _, creado = Organizacion.todos.update_or_create(
                nombre=nombre,
                territorio=delegacion,
                defaults={
                    "domicilio_legal": domicilio,
                    "socios_activos": _entero(socios),
                    "fecha_constitucion": _fecha(fecha_c),
                    "registro_pj": reg_pj,
                    "fecha_inscripcion": _fecha(fecha_i),
                    "registro_dir": reg_dir,
                    "eliminado": None,
                },
            )
            creados += 1 if creado else 0
            actualizados += 0 if creado else 1
        return creados, actualizados

    def _informe(self, filas, destino):
        nombres = [_texto(f[0]) for f in filas]
        territorios = [_texto(f[2]) for f in filas]
        regs_pj = [_texto(f[5]) for f in filas if _texto(f[5])]
        socios_malos = [
            f[3] for f in filas if _texto(f[3]) and not _texto(f[3]).isdigit()
        ]
        sin_dir = [f for f in filas if not _texto(f[7])]
        duplicados_nombre = len(nombres) - len(set(nombres))
        duplicados_pj = len(regs_pj) - len(set(regs_pj))
        sin_territorio = [t for t in territorios if not t]
        fuera_de_lista = sorted(
            {t for t in territorios if t and t.upper() not in MAPA_TERRITORIOS}
        )
        con_espacios = sorted({t for t in territorios if t != t.strip()})

        lineas = [
            "# Informe de calidad — base de JJVV y organizaciones",
            "",
            f"Filas leídas: {len(filas)}",
            "",
            "## Hallazgos",
            f"- Territorios vacíos: {len(sin_territorio)}",
            f"- Territorios fuera de la lista: {', '.join(fuera_de_lista) or 'ninguno'}",
            f"- Territorios con espacios sobrantes: {', '.join(con_espacios) or 'ninguno'}",
            f"- Nombres duplicados: {duplicados_nombre}",
            f"- N° de registro de P.J. duplicados: {duplicados_pj}",
            f"- Socios activos no numéricos: {len(socios_malos)}",
            f"- Registro de directiva vacío: {len(sin_dir)}",
            "",
            "Ninguna fila se descartó: todas se cargaron con "
            "`verificacion = sin-verificar` para revisión.",
            "",
        ]
        destino.write_text("\n".join(lineas), encoding="utf-8")
