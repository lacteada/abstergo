"""Vistas de la API `v1`: CRUD con borrado lógico, autenticación y recuperación."""

import hmac

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.core.mail import send_mail
from django.utils import timezone
from drf_spectacular.utils import extend_schema
from rest_framework import status, viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

from apps.atenciones.models import Atencion
from apps.catalogos.models import Meta as MetaModel
from apps.catalogos.models import SubAtencion, TipoAtencion
from apps.ciudadanos.models import Vecino
from apps.cuentas.models import RecuperacionPassword, Rol
from apps.organizacion.models import Delegacion

from .permissions import PermisoPorRol
from .serializers import (
    AtencionSerializer,
    DelegacionSerializer,
    DetalleSerializer,
    LogoutSerializer,
    MetaSerializer,
    NuevaPasswordSerializer,
    PerfilSerializer,
    RecuperarSerializer,
    RolSerializer,
    SubAtencionSerializer,
    TipoAtencionSerializer,
    UsuarioSerializer,
    ValidarSerializer,
    VecinoSerializer,
)

Usuario = get_user_model()


class BaseViewSet(viewsets.ModelViewSet):
    """CRUD con borrado lógico. El permiso sale de la matriz, vía `modulo`."""

    permission_classes = [IsAuthenticated, PermisoPorRol]
    modulo = None

    def perform_destroy(self, instance):
        instance.eliminar()


class RolViewSet(BaseViewSet):
    queryset = Rol.objects.all()
    serializer_class = RolSerializer
    modulo = "roles"


class UsuarioViewSet(BaseViewSet):
    queryset = Usuario.objects.all()
    serializer_class = UsuarioSerializer
    modulo = "usuarios"

    def get_queryset(self):
        # `Usuario.objects` es un UserManager: no filtra el borrado lógico.
        return Usuario.objects.filter(eliminado__isnull=True)


class DelegacionViewSet(BaseViewSet):
    queryset = Delegacion.objects.all()
    serializer_class = DelegacionSerializer
    modulo = "delegaciones"


class MetaViewSet(BaseViewSet):
    queryset = MetaModel.objects.all()
    serializer_class = MetaSerializer
    modulo = "metas"


class TipoAtencionViewSet(BaseViewSet):
    queryset = TipoAtencion.objects.all()
    serializer_class = TipoAtencionSerializer
    modulo = "tipos"


class SubAtencionViewSet(BaseViewSet):
    queryset = SubAtencion.objects.all()
    serializer_class = SubAtencionSerializer
    modulo = "subatenciones"


class VecinoViewSet(BaseViewSet):
    queryset = Vecino.objects.all()
    serializer_class = VecinoSerializer
    modulo = "vecinos"


class AtencionViewSet(BaseViewSet):
    queryset = Atencion.objects.select_related("vecino", "tipo_atencion")
    serializer_class = AtencionSerializer
    modulo = "atenciones"


class MeView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(responses=PerfilSerializer)
    def get(self, request):
        return Response(PerfilSerializer(request.user).data)


class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(request=LogoutSerializer, responses={205: None})
    def post(self, request):
        serializer = LogoutSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            RefreshToken(serializer.validated_data["refresh"]).blacklist()
        except Exception:
            return Response({"detail": "Token inválido."}, status=400)
        return Response(status=status.HTTP_205_RESET_CONTENT)


def _enviar_codigo(usuario, codigo):
    send_mail(
        subject="Código de recuperación",
        message=(
            f"Tu código es {codigo}. "
            f"Vence en {settings.OTP_EXPIRY_MINUTES} minutos."
        ),
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[usuario.email],
        fail_silently=True,
    )


class RecuperarPasswordView(APIView):
    permission_classes = []

    @extend_schema(request=RecuperarSerializer, responses=DetalleSerializer)
    def post(self, request):
        serializer = RecuperarSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data["email"]
        usuario = Usuario.objects.filter(
            email__iexact=email, eliminado__isnull=True
        ).first()
        if usuario:
            recuperacion = RecuperacionPassword.generar(usuario)
            _enviar_codigo(usuario, recuperacion.codigo)
        # Misma respuesta exista o no el correo: no se revela qué cuentas hay.
        return Response({"detail": "Si el correo existe, se envió un código."})


class ValidarCodigoView(APIView):
    permission_classes = []

    @extend_schema(request=ValidarSerializer, responses=DetalleSerializer)
    def post(self, request):
        serializer = ValidarSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data["email"]
        codigo = serializer.validated_data["codigo"]
        usuario = Usuario.objects.filter(
            email__iexact=email, eliminado__isnull=True
        ).first()
        recuperacion = None
        if usuario:
            recuperacion = (
                RecuperacionPassword.objects.filter(usuario=usuario, usado__isnull=True)
                .order_by("-creado")
                .first()
            )
        if not recuperacion or not recuperacion.vigente():
            return Response({"detail": "Código inválido o vencido."}, status=400)
        if not hmac.compare_digest(recuperacion.codigo, codigo):
            recuperacion.intentos += 1
            recuperacion.save(update_fields=["intentos"])
            return Response({"detail": "Código inválido o vencido."}, status=400)
        recuperacion.validado = timezone.now()
        recuperacion.save(update_fields=["validado"])
        return Response({"detail": "Código válido."})


class NuevaPasswordView(APIView):
    permission_classes = []

    @extend_schema(request=NuevaPasswordSerializer, responses=DetalleSerializer)
    def post(self, request):
        serializer = NuevaPasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data["email"]
        codigo = serializer.validated_data["codigo"]
        password = serializer.validated_data["password"]
        usuario = Usuario.objects.filter(
            email__iexact=email, eliminado__isnull=True
        ).first()
        recuperacion = None
        if usuario:
            recuperacion = (
                RecuperacionPassword.objects.filter(
                    usuario=usuario, usado__isnull=True, validado__isnull=False
                )
                .order_by("-creado")
                .first()
            )
        if not recuperacion or not recuperacion.vigente():
            return Response({"detail": "Código inválido o vencido."}, status=400)
        if not hmac.compare_digest(recuperacion.codigo, codigo):
            return Response({"detail": "Código inválido o vencido."}, status=400)
        try:
            validate_password(password, usuario)
        except ValidationError as exc:
            return Response({"detail": list(exc.messages)}, status=400)
        usuario.set_password(password)
        usuario.save(update_fields=["password"])
        recuperacion.usado = timezone.now()
        recuperacion.save(update_fields=["usado"])
        return Response({"detail": "Contraseña actualizada."})
