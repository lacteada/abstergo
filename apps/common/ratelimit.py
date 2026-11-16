"""Límite simple de intentos de login por IP (RNF-003, R9).

Cuenta los POST a los endpoints de login dentro de una ventana de tiempo y
responde 429 al superar el máximo. Se activa solo sin DEBUG, así no interfiere
con el servidor local ni con las pruebas.
"""

from django.conf import settings
from django.core.cache import cache
from django.http import HttpResponse

RUTAS_LOGIN = ("/login/", "/api/v1/auth/login/")


class LimiteIntentos:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if (
            not settings.DEBUG
            and request.method == "POST"
            and request.path in RUTAS_LOGIN
        ):
            ip = request.META.get("REMOTE_ADDR", "sin-ip")
            clave = f"login-intentos:{ip}:{request.path}"
            intentos = cache.get(clave, 0)
            if intentos >= settings.LOGIN_INTENTOS_MAX:
                return HttpResponse(
                    "Demasiados intentos de acceso. Intenta más tarde.", status=429
                )
            cache.set(clave, intentos + 1, settings.LOGIN_INTENTOS_VENTANA)
        return self.get_response(request)
