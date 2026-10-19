"""Estado textual de los registros del mantenedor.

Se distingue del borrado lógico (`eliminado`): `estado` es el dato de negocio
que se muestra en la tabla y se exporta; `eliminado` es la fila retirada del
sistema. El mantenedor edita el primero; el segundo lo marca la baja.
"""

from django.db import models

ACTIVO = "activo"
INACTIVO = "inactivo"

ESTADOS = [
    (ACTIVO, "Activo"),
    (INACTIVO, "Inactivo"),
]


class ConEstado(models.Model):
    """Aporta la columna `estado` con sus dos valores."""

    estado = models.CharField(
        "estado", max_length=10, choices=ESTADOS, default=ACTIVO
    )

    class Meta:
        abstract = True

    @property
    def esta_vigente(self):
        """Activo y no dado de baja: lo que el formulario de atención ofrece."""
        return self.eliminado is None and self.estado == ACTIVO
