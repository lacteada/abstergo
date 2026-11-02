from django.apps import AppConfig
from django.db.models.signals import post_migrate


class CuentasConfig(AppConfig):
    name = 'apps.cuentas'
    verbose_name = 'Cuentas'

    def ready(self):
        # Importar acá conecta las señales `post_save`; el `post_migrate` deja
        # los grupos espejo tras cada migración.
        from apps.cuentas import signals

        post_migrate.connect(
            signals.sincronizar_grupos, sender=self, dispatch_uid="cuentas.grupos"
        )
