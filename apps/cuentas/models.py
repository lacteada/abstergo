import secrets
from datetime import timedelta

from django.conf import settings
from django.contrib.auth.models import AbstractUser, UserManager
from django.db import models
from django.utils import timezone

from apps.common.soft_delete import BorradoLogico, Eliminado
from apps.common.validators import validar_catalogo, validar_codigo, validar_nombre


class Rol(BorradoLogico):
    codigo = models.SlugField(
        "código",
        max_length=40,
        unique=True,
        null=True,
        blank=True,
        validators=[validar_codigo],
    )
    nombre = models.CharField(
        "nombre", max_length=60, unique=True, validators=[validar_nombre]
    )
    descripcion = models.CharField(
        "descripción", max_length=200, blank=True, validators=[validar_catalogo]
    )

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
    # Cuando el perfil trabaja en más de un territorio. `delegacion` sigue
    # siendo la principal; esta es la lista completa de las autorizadas que el
    # selector de contexto puede ofrecer.
    delegaciones_autorizadas = models.ManyToManyField(
        "organizacion.Delegacion",
        blank=True,
        related_name="usuarios_autorizados",
        verbose_name="delegaciones autorizadas",
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

    @property
    def pendiente(self):
        """Cuenta creada sin contraseña: falta que active con el enlace.

        El administrador no define la clave; hasta que la persona entra al
        enlace del correo, la cuenta no tiene contraseña usable y no puede
        iniciar sesión.
        """
        return not self.has_usable_password()

    @property
    def estado_texto(self):
        """Estado para la tabla y la ficha: Pendiente, Activo o Inactivo."""
        if self.pendiente:
            return "Pendiente"
        return "Activo" if self.is_active else "Inactivo"

    @property
    def delegaciones_texto(self):
        """Las autorizadas en una línea; si no hay, la principal.

        La usan la ficha de consulta y la exportación, para no repetir el
        recorrido por la relación en cada lugar.
        """
        autorizadas = list(self.delegaciones_autorizadas.all())
        if autorizadas:
            return ", ".join(delegacion.nombre for delegacion in autorizadas)
        return self.delegacion.nombre if self.delegacion_id else ""

    def clean(self):
        # AbstractBaseUser.clean() normaliza el USERNAME_FIELD, y
        # normalize_username(None) revienta. Sin correo no hay qué normalizar.
        if self.email:
            super().clean()

    @classmethod
    def vigentes(cls):
        """Los usuarios no dados de baja.

        `objects` es un UserManager, que no filtra por borrado lógico; esta es la
        única forma de pedir los vigentes.
        """
        return cls.objects.filter(eliminado__isnull=True)


class RecuperacionPassword(models.Model):
    """Código de recuperación de contraseña.

    Antes vivía en la sesión de la web; el cliente móvil no tiene sesión, así
    que el código persiste. Se guarda en claro a propósito: son 6 dígitos con
    vencimiento corto y tope de intentos.
    """

    MAX_INTENTOS = 5

    usuario = models.ForeignKey(
        "cuentas.Usuario",
        on_delete=models.CASCADE,
        related_name="recuperaciones",
        verbose_name="usuario",
    )
    codigo = models.CharField("código", max_length=6)
    creado = models.DateTimeField("creado", auto_now_add=True)
    expira = models.DateTimeField("expira")
    validado = models.DateTimeField("validado", null=True, blank=True)
    usado = models.DateTimeField("usado", null=True, blank=True)
    intentos = models.PositiveIntegerField("intentos", default=0)

    class Meta:
        verbose_name = "recuperación de contraseña"
        verbose_name_plural = "recuperaciones de contraseña"
        ordering = ["-creado"]

    def __str__(self):
        return f"Recuperación de {self.usuario} ({self.creado:%d-%m-%Y %H:%M})"

    def vigente(self):
        return (
            self.usado is None
            and self.intentos < self.MAX_INTENTOS
            and timezone.now() < self.expira
        )

    @classmethod
    def generar(cls, usuario):
        codigo = f"{secrets.randbelow(1000000):06d}"
        vence = timezone.now() + timedelta(minutes=settings.OTP_EXPIRY_MINUTES)
        return cls.objects.create(usuario=usuario, codigo=codigo, expira=vence)
