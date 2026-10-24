"""Clave técnica derivada del nombre.

`codigo` no es un dato que el usuario escriba: es la llave estable que usan el
cargador de datos (`datos_nuevos/`) y los buscadores. El mantenedor solo pide el
nombre, y el código se deriva de él la primera vez, igual que hicieron las
migraciones que rellenaron lo ya cargado.

Se ignora si viene indicado: `cargar_datos` lo trae en el JSON y debe seguir
mandando, o la carga dejaría de ser idempotente.
"""

from django.db import models
from django.utils.text import slugify


class ConCodigoDerivado(models.Model):
    """Deriva `codigo` del nombre cuando no viene indicado."""

    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        if not self.codigo:
            self.codigo = self._codigo_derivado()
        super().save(*args, **kwargs)

    def _codigo_derivado(self):
        """Un slug del nombre, único entre los registros del modelo.

        El sufijo numérico evita el choque contra la restricción única cuando
        dos nombres distintos rinden el mismo slug.
        """
        base = slugify(self.nombre)[:40] or "registro"
        modelo = type(self)
        codigo = base
        sufijo = 1
        while modelo._base_manager.filter(codigo=codigo).exclude(pk=self.pk).exists():
            sufijo += 1
            codigo = f"{base[: 40 - len(str(sufijo)) - 1]}-{sufijo}"
        return codigo
