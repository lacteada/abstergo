"""Puerta de calidad portable: pruebas reales, salida JSON firmada y log por comprobación.

No ejecuta comandos desde la web. Requiere SECRET_KEY del entorno que mostrará
el reporte; cada comprobación usa una base SQLite temporal, nunca producción.
"""

import argparse
import json
import os
import subprocess
import sys
import tempfile
import time
import xml.etree.ElementTree as ET
from datetime import UTC, datetime
from pathlib import Path

from dotenv import load_dotenv

RAIZ = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--salida", type=Path, default=RAIZ / "var/calidad.json")
    args = parser.parse_args()
    load_dotenv(RAIZ / ".env")
    if not os.environ.get("SECRET_KEY"):
        parser.error("Configura SECRET_KEY para firmar el reporte del entorno.")
    destino = args.salida.resolve()
    destino.parent.mkdir(parents=True, exist_ok=True)
    logs = destino.parent / "comprobaciones"
    logs.mkdir(exist_ok=True)
    (logs / "pytest.xml").unlink(missing_ok=True)
    resultados = []
    with tempfile.TemporaryDirectory(prefix="abstergo-calidad-") as temporal:
        carpeta = Path(temporal)
        (carpeta / "settings_verif.py").write_text(
            "from config.settings import *\n"
            "from pathlib import Path\n"
            "ALLOWED_HOSTS=['testserver','localhost','127.0.0.1']\n"
            "DATABASES={'default':{'ENGINE':'django.db.backends.sqlite3',"
            "'NAME':str(Path(__file__).with_name('verif.sqlite3'))}}\n"
            "MEDIA_ROOT=str(Path(__file__).with_name('media'))\n",
            encoding="utf-8",
        )
        entorno = dict(os.environ)
        entorno.update(
            DJANGO_SETTINGS_MODULE="settings_verif",
            PYTHONUTF8="1",
            PYTHONPATH=os.pathsep.join([temporal, str(RAIZ)]),
            MAILER_BACKEND="django.core.mail.backends.console.EmailBackend",
            USUARIOS_PASSWORD_INICIAL="Clave.Verificacion1",
            DEBUG="True",
        )
        pasos = [
            ("Configuración Django", ["manage.py", "check"]),
            ("Migraciones completas", ["manage.py", "makemigrations", "--check", "--dry-run"]),
            ("Aplicación de migraciones", ["manage.py", "migrate", "--noinput"]),
            ("Carga de catálogos", ["manage.py", "cargar_datos"]),
            ("Análisis estático Ruff", ["-m", "ruff", "check", "."]),
            ("Pruebas automatizadas", ["-m", "pytest", "-q", f"--junitxml={logs / 'pytest.xml'}"]),
            (
                "Dependencias conocidas",
                [
                    "-m",
                    "pip_audit",
                    "-r",
                    "requirements.txt",
                    "--progress-spinner",
                    "off",
                    "--format",
                    "json",
                ],
            ),
        ]
        # Mismo bloque smoke que utiliza la verificación Linux oficial.
        fuente = (RAIZ / "scripts/verificar.sh").read_text(encoding="utf-8")
        smoke = fuente.split("\"$PY\" - <<'PY'\n", 1)[1].split("\nPY", 1)[0]
        pasos.append(("Rutas y API con permisos", ["-c", smoke]))
        for numero, (nombre, comando) in enumerate(pasos, 1):
            print(f"[{numero}/{len(pasos)}] {nombre}", flush=True)
            inicio = time.monotonic()
            try:
                proceso = subprocess.run(
                    [sys.executable, *comando],
                    cwd=RAIZ,
                    env=entorno,
                    capture_output=True,
                    text=True,
                    encoding="utf-8",
                    errors="replace",
                    timeout=600,
                )
                codigo = proceso.returncode
                salida = proceso.stdout + proceso.stderr
            except subprocess.TimeoutExpired:
                codigo, salida = 124, "Tiempo máximo excedido."
            (logs / f"{numero:02d}.txt").write_text(salida, encoding="utf-8")
            resultados.append(
                {
                    "nombre": nombre,
                    "correcto": codigo == 0,
                    "codigo": codigo,
                    "segundos": round(time.monotonic() - inicio, 2),
                }
            )
        conteo = {"total": 0, "fallos": 0, "errores": 0, "omitidas": 0}
        if (logs / "pytest.xml").exists():
            suites = ET.parse(logs / "pytest.xml").getroot().iter("testsuite")
            for suite in suites:
                for clave, atributo in [
                    ("total", "tests"),
                    ("fallos", "failures"),
                    ("errores", "errors"),
                    ("omitidas", "skipped"),
                ]:
                    conteo[clave] += int(suite.get(atributo, 0))
        sys.path[:0] = [temporal, str(RAIZ)]
        os.environ.update({k: entorno[k] for k in ["DJANGO_SETTINGS_MODULE", "MAILER_BACKEND"]})
        import django

        django.setup()
        from django.core import signing

        from apps.panel.calidad import SALT, huella_fuentes

        revision = subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=RAIZ, text=True
        ).strip()
        reporte = {
            "fecha": datetime.now(UTC).isoformat(),
            "revision": revision,
            "huella": huella_fuentes(RAIZ),
            "arbol_modificado": bool(
                subprocess.check_output(
                    ["git", "status", "--porcelain"],
                    cwd=RAIZ,
                ).strip()
            ),
            "entorno": "SQLite temporal de verificación",
            "correcto": all(r["correcto"] for r in resultados),
            "pruebas": conteo,
            "comprobaciones": resultados,
        }
        sobre = {"reporte": reporte, "firma": signing.dumps(reporte, salt=SALT)}
        provisional = destino.with_suffix(".tmp")
        provisional.write_text(json.dumps(sobre, ensure_ascii=False, indent=2), encoding="utf-8")
        provisional.replace(destino)
        print(json.dumps(reporte, ensure_ascii=False, indent=2))
        return 0 if reporte["correcto"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
