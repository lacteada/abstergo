"""Evidencia reproducible de calidad, de solo lectura y con procedencia verificable."""

import hashlib
import json
import subprocess
from datetime import UTC, datetime, timedelta
from pathlib import Path

from django.conf import settings
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core import signing
from django.http import HttpResponse, HttpResponseForbidden
from django.utils.decorators import method_decorator
from django.views.decorators.cache import never_cache
from django.views.generic import TemplateView

from apps.common.permisos import puede

SALT = "abstergo.calidad.v1"


def huella_fuentes(raiz=None):
    raiz = Path(raiz or settings.BASE_DIR)
    resultado = subprocess.run(
        ["git", "ls-files", "--cached", "--others", "--exclude-standard", "-z"],
        cwd=raiz,
        capture_output=True,
        check=True,
        timeout=10,
    )
    huella = hashlib.sha256()
    extensiones = {".py", ".html", ".css", ".js", ".sh", ".yml", ".toml"}
    for nombre in sorted(set(resultado.stdout.decode().split("\0")) - {""}):
        archivo = raiz / nombre
        if archivo.suffix in extensiones or nombre in {"requirements.txt", "requirements-dev.txt"}:
            huella.update(nombre.encode())
            huella.update(archivo.read_bytes() if archivo.exists() else b"ELIMINADO")
    return huella.hexdigest()


def cargar_reporte():
    try:
        sobre = json.loads(settings.QUALITY_REPORT_PATH.read_text(encoding="utf-8"))
        reporte = signing.loads(sobre["firma"], salt=SALT)
        if reporte != sobre["reporte"]:
            raise ValueError("contenido alterado")
        return reporte
    except (OSError, ValueError, KeyError, signing.BadSignature):
        return None


@method_decorator(never_cache, name="dispatch")
class Calidad(LoginRequiredMixin, TemplateView):
    template_name = "panel/calidad.html"

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated and not puede(request.user, "quality"):
            return HttpResponseForbidden("Tu perfil no tiene permiso para consultar calidad.")
        return super().dispatch(request, *args, **kwargs)

    def get(self, request, *args, **kwargs):
        if request.GET.get("descargar") == "1":
            reporte = cargar_reporte()
            if not reporte:
                return HttpResponse("No hay un reporte válido disponible.", status=404)
            respuesta = HttpResponse(
                json.dumps(reporte, indent=2, ensure_ascii=False),
                content_type="application/json",
            )
            respuesta["Content-Disposition"] = 'attachment; filename="evidencia_calidad.json"'
            return respuesta
        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        contexto = super().get_context_data(**kwargs)
        reporte = cargar_reporte()
        vigente = False
        antiguedad = False
        if reporte:
            try:
                vigente = reporte["huella"] == huella_fuentes()
                antiguedad = datetime.now(UTC) - datetime.fromisoformat(
                    reporte["fecha"]
                ) > timedelta(days=7)
            except (OSError, ValueError, KeyError, subprocess.SubprocessError):
                vigente = False
        contexto.update(
            seccion="calidad",
            reporte=reporte,
            vigente=vigente,
            antiguo=antiguedad,
            https=self.request.is_secure(),
            debug=settings.DEBUG,
            cookie_segura=settings.SESSION_COOKIE_SECURE,
            mfa_configurada=bool(settings.MFA_ENCRYPTION_KEY),
        )
        return contexto
