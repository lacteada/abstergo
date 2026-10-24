"""Código visible de un registro, generado una sola vez.

Tres cosas distintas conviven en un registro y conviene no confundirlas:

- ``id``: la clave primaria. Interna; no se muestra ni se escribe.
- ``codigo``: la llave técnica del cargador de datos (``datos_nuevos/``).
- ``referencia``: el código que ve el usuario, del tipo ``DEL-01``.

La referencia se deriva de la clave primaria, así que es única por
construcción, **inmutable** (el ``pk`` no cambia nunca) y no tiene condición de
carrera entre procesos: dos altas simultáneas no pueden calcular el mismo
número. Es lo que el PDF pide como identificador de una actividad.
"""

from django.db import models


class ConReferencia(models.Model):
    """Aporta el campo ``referencia`` y lo llena al primer guardado."""

    # Lo define cada entidad. Es el prefijo del código: DEL, AT, ROL…
    PREFIJO = "REG"

    referencia = models.CharField(
        "código", max_length=12, unique=True, null=True, blank=True, editable=False
    )

    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        # El pk recién existe después del primer guardado, así que la
        # referencia se escribe en una segunda pasada y solo la primera vez.
        super().save(*args, **kwargs)
        if not self.referencia:
            self.referencia = f"{self.PREFIJO}-{self.pk:02d}"
            # La segunda pasada es una actualización de un solo campo: conserva
            # `using` del llamador y no vuelve a insertar.
            kwargs["update_fields"] = ["referencia"]
            kwargs.pop("force_insert", None)
            super().save(*args, **kwargs)
