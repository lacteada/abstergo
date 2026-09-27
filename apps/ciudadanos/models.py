from django.db import models


class Vecino(models.Model):
    ACTIVO = "Activo"
    INACTIVO = "Inactivo"
    ESTADOS = [(ACTIVO, "Activo"), (INACTIVO, "Inactivo")]

    nombre = models.CharField("nombre", max_length=120)
    rut = models.CharField("RUT", max_length=15, unique=True)
    direccion = models.CharField("dirección", max_length=200, blank=True)
    telefono = models.CharField("teléfono", max_length=30, blank=True)
    territorio = models.ForeignKey(
        "organizacion.Delegacion",
        on_delete=models.PROTECT,
        related_name="vecinos",
        verbose_name="territorio",
    )
    tipo_gestion = models.CharField("tipo de gestión", max_length=80, blank=True)
    estado = models.CharField(
        "estado", max_length=10, choices=ESTADOS, default=ACTIVO
    )

    class Meta:
        verbose_name = "vecino"
        verbose_name_plural = "vecinos"
        ordering = ["nombre"]

    def __str__(self):
        return f"{self.nombre} ({self.rut})"
