from django.db import models
from django.utils import timezone


class TodosManager(models.Manager):
    """Ve también los eliminados."""


class ActivosManager(models.Manager):
    """Por defecto no muestra los eliminados."""

    def get_queryset(self):
        return super().get_queryset().filter(eliminado__isnull=True)


class Eliminado(models.Model):
    """Marca la fila con una fecha en vez de borrarla.

    Solo aporta el campo y el método. Es la mitad que necesita Usuario, que
    no puede cambiar su gestor: `objects` tiene que seguir siendo un
    UserManager para que funcionen `createsuperuser` y `authenticate`.
    """

    eliminado = models.DateTimeField("eliminado", null=True, blank=True)

    class Meta:
        abstract = True

    def eliminar(self):
        self.eliminado = timezone.now()
        self.save(update_fields=["eliminado"])


class BorradoLogico(Eliminado):
    """Eliminado más los dos gestores.

    La usan las entidades que otras referencian: así el mantenedor puede
    quitarlas de circulación sin que se pierda la referencia de quien apuntaba
    a ellas.
    """

    objects = ActivosManager()
    todos = TodosManager()

    class Meta:
        abstract = True
