"""El despliegue no debe aprobar sin una llave MFA válida."""

from cryptography.fernet import Fernet
from django.conf import settings
from django.core.checks import Error, Tags, register


@register(Tags.security, deploy=True)
def llave_mfa(app_configs, **kwargs):
    try:
        Fernet(settings.MFA_ENCRYPTION_KEY.encode())
    except (ValueError, AttributeError):
        return [
            Error(
                "MFA_ENCRYPTION_KEY falta o no es una llave Fernet válida.",
                hint="Genera y respalda una llave independiente fuera del repositorio.",
                id="cuentas.E001",
            )
        ]
    return []
