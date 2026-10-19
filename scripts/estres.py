#!/usr/bin/env python3
"""Prueba de carga del sistema desplegado.

Sube la concurrencia por etapas y mide latencia promedio, percentil 95,
solicitudes por segundo y errores, contra una URL real (AWS). No reemplaza las
pruebas funcionales: solo mide cuánto aguanta el entorno. Usa solo la
biblioteca estándar, sin dependencias nuevas.

Ejemplo:

    python scripts/estres.py --url http://18.209.251.129 --niveles 5,10,20,40 \
        --duracion 20 --salida documentacion/estres.md
"""

from __future__ import annotations

import argparse
import json
import statistics
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field

# Umbrales de aceptación definidos de antemano, para poder decidir con el dato.
UMBRALES = {
    "latencia_p95_ms": 1500.0,
    "tasa_error_pct": 1.0,
}


@dataclass
class Resultado:
    nivel: int
    latencias: list[float] = field(default_factory=list)
    errores: int = 0
    duracion: float = 0.0

    @property
    def total(self) -> int:
        return len(self.latencias) + self.errores

    @property
    def rps(self) -> float:
        return self.total / self.duracion if self.duracion else 0.0

    @property
    def promedio_ms(self) -> float:
        return statistics.fmean(self.latencias) if self.latencias else 0.0

    @property
    def p95_ms(self) -> float:
        if not self.latencias:
            return 0.0
        ordenadas = sorted(self.latencias)
        indice = min(len(ordenadas) - 1, int(round(0.95 * (len(ordenadas) - 1))))
        return ordenadas[indice]

    @property
    def tasa_error_pct(self) -> float:
        return 100.0 * self.errores / self.total if self.total else 0.0

    def aprueba(self) -> bool:
        return (
            self.p95_ms <= UMBRALES["latencia_p95_ms"]
            and self.tasa_error_pct <= UMBRALES["tasa_error_pct"]
        )


def _una_peticion(url: str, timeout: float) -> float | None:
    """Devuelve la latencia en milisegundos, o None si falló."""
    inicio = time.perf_counter()
    try:
        with urllib.request.urlopen(url, timeout=timeout) as respuesta:
            respuesta.read()
        return (time.perf_counter() - inicio) * 1000
    except (urllib.error.URLError, TimeoutError, OSError):
        return None


def _trabajador(url: str, fin: float, timeout: float, resultado: Resultado):
    while time.perf_counter() < fin:
        latencia = _una_peticion(url, timeout)
        if latencia is None:
            resultado.errores += 1
        else:
            resultado.latencias.append(latencia)


def medir(url: str, nivel: int, duracion: float, timeout: float) -> Resultado:
    resultado = Resultado(nivel=nivel)
    inicio = time.perf_counter()
    fin = inicio + duracion
    with ThreadPoolExecutor(max_workers=nivel) as ejecutor:
        for _ in range(nivel):
            ejecutor.submit(_trabajador, url, fin, timeout, resultado)
    resultado.duracion = time.perf_counter() - inicio
    return resultado


def _fila(r: Resultado) -> str:
    estado = "APRUEBA" if r.aprueba() else "NO APRUEBA"
    return (
        f"| {r.nivel} | {r.total} | {r.rps:.1f} | {r.promedio_ms:.0f} | "
        f"{r.p95_ms:.0f} | {r.tasa_error_pct:.1f}% | {estado} |"
    )


def main() -> int:
    analizador = argparse.ArgumentParser(description=__doc__)
    analizador.add_argument("--url", required=True, help="Base, p. ej. http://host")
    analizador.add_argument("--ruta", default="/login/", help="Ruta a probar")
    analizador.add_argument(
        "--niveles", default="5,10,20,40", help="Concurrencias separadas por coma"
    )
    analizador.add_argument("--duracion", type=float, default=20.0, help="Segundos por nivel")
    analizador.add_argument("--timeout", type=float, default=10.0)
    analizador.add_argument("--salida", help="Archivo Markdown donde anexar la tabla")
    args = analizador.parse_args()

    url = args.url.rstrip("/") + args.ruta
    niveles = [int(n) for n in args.niveles.split(",") if n.strip()]
    filas = [
        "| Concurrencia | Solicitudes | RPS | Latencia prom. (ms) "
        "| P95 (ms) | Errores | Veredicto |",
        "|---|---|---|---|---|---|---|",
    ]
    resumen = {"url": url, "niveles": [], "umbrales": UMBRALES}

    print(f"Objetivo: {url}")
    print(f"Umbrales: {UMBRALES}\n")
    for nivel in niveles:
        resultado = medir(url, nivel, args.duracion, args.timeout)
        fila = _fila(resultado)
        filas.append(fila)
        print(fila)
        resumen["niveles"].append(
            {
                "concurrencia": resultado.nivel,
                "solicitudes": resultado.total,
                "rps": round(resultado.rps, 2),
                "promedio_ms": round(resultado.promedio_ms, 1),
                "p95_ms": round(resultado.p95_ms, 1),
                "errores": resultado.errores,
                "tasa_error_pct": round(resultado.tasa_error_pct, 2),
                "aprueba": resultado.aprueba(),
            }
        )

    print("\nJSON:")
    print(json.dumps(resumen, ensure_ascii=False, indent=2))

    if args.salida:
        with open(args.salida, "a", encoding="utf-8") as archivo:
            archivo.write(f"\n### {time.strftime('%Y-%m-%d %H:%M')} · {url}\n\n")
            archivo.write("\n".join(filas) + "\n")
        print(f"\nTabla anexada a {args.salida}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
