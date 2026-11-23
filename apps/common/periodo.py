"""El período activo, hermano de la delegación activa.

Cada usuario elige con qué período trabaja desde la top bar; si no elige
ninguno, es el más reciente. La elección vive en la sesión, igual que la
delegación: así toda la aplicación (tableros, dashboard, fichas) muestra el
mismo período.
"""

from apps.sgr.models import Periodo

CLAVE_SESION = "periodo_activo"


def disponibles():
    """Los períodos cargados, del más reciente al más antiguo."""
    return Periodo.objects.all()


def activa(request):
    """El período elegido en la sesión, validado; si no, el más reciente."""
    elegido = getattr(request, "session", {}).get(CLAVE_SESION) if request else None
    if elegido:
        periodo = Periodo.objects.filter(pk=elegido).first()
        if periodo:
            return periodo
    return disponibles().first()


def cambiar(request, valor):
    """Fija el período activo de la sesión, si existe; vacío lo reinicia."""
    if not valor:
        request.session.pop(CLAVE_SESION, None)
    elif Periodo.objects.filter(pk=valor).exists():
        request.session[CLAVE_SESION] = int(valor)
