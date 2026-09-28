from django.contrib.auth.models import AbstractUser, UserManager
from django.db import models

from apps.common.soft_delete import BorradoLogico, Eliminado


class Rol(BorradoLogico):
    nombre = models.CharField("nombre", max_length=60, unique=True)
    descripcion = models.CharField("descripción", max_length=200, blank=True)

    class Meta:
        verbose_name = "rol"
        verbose_name_plural = "roles"
        ordering = ["nombre"]

    def __str__(self):
        return self.nombre


class UsuarioManager(UserManager):
    """UserManager con el correo como identificador.

    El de Django recibe `username` como primer argumento y lo exige; con
    USERNAME_FIELD apuntando al correo, `createsuperuser` no pasaría.
    """

    def create_user(self, email=None, password=None, **extra_fields):
        if not email:
            raise ValueError("El correo es obligatorio.")
        usuario = self.model(email=self.normalize_email(email), **extra_fields)
        usuario.set_password(password)
        usuario.save(using=self._db)
        return usuario

    def create_superuser(self, email=None, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        return self.create_user(email, password, **extra_fields)


class Usuario(AbstractUser, Eliminado):
    """El usuario del sistema.

    Sin `username`: la llave es el `id` y el correo es un dato más, editable.
    Hereda de `Eliminado` y no de `BorradoLogico` porque `objects` tiene que
    seguir siendo un UserManager.

    El correo admite nulos para que varios usuarios puedan no tener. En MySQL
    el índice único deja convivir varios NULL. Un usuario sin correo no puede
    iniciar sesión; su contraseña queda inutilizable.
    """

    username = None
    email = models.EmailField("correo", unique=True, null=True, blank=True)
    rol = models.ForeignKey(
        Rol,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="usuarios",
        verbose_name="rol",
    )
    delegacion = models.ForeignKey(
        "organizacion.Delegacion",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="usuarios",
        verbose_name="delegación",
    )

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    objects = UsuarioManager()

    class Meta:
        verbose_name = "usuario"
        verbose_name_plural = "usuarios"
        ordering = ["first_name", "last_name"]

    def __str__(self):
        return self.get_full_name() or self.email or f"Usuario {self.pk}"

    def clean(self):
        # AbstractBaseUser.clean() normaliza el USERNAME_FIELD, y
        # normalize_username(None) revienta. Sin correo no hay qué normalizar.
        if self.email:
            super().clean()
