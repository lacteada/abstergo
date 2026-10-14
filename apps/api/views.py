"""Vistas de la API `v1`: CRUD con borrado lógico, autenticación y recuperación."""

from django.contrib.auth import get_user_model
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
from apps.cuentas import otp
from apps.cuentas.models import Rol
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
    # El router exige `queryset` para nombrar las rutas; `get_queryset` manda.
    queryset = Usuario.objects.all()
    serializer_class = UsuarioSerializer
    modulo = "users"

    def get_queryset(self):
        return Usuario.vigentes()


class DelegacionViewSet(BaseViewSet):
    queryset = Delegacion.objects.all()
    serializer_class = DelegacionSerializer
    modulo = "delegations"


class MetaViewSet(BaseViewSet):
    queryset = MetaModel.objects.all()
    serializer_class = MetaSerializer
    modulo = "goals"


class TipoAtencionViewSet(BaseViewSet):
    queryset = TipoAtencion.objects.all()
    serializer_class = TipoAtencionSerializer
    modulo = "attention_types"


class SubAtencionViewSet(BaseViewSet):
    queryset = SubAtencion.objects.all()
    serializer_class = SubAtencionSerializer
    modulo = "attention_subtypes"


class VecinoViewSet(BaseViewSet):
    queryset = Vecino.objects.all()
    serializer_class = VecinoSerializer
    modulo = "neighbors"


class AtencionViewSet(BaseViewSet):
    queryset = Atencion.objects.select_related("vecino", "tipo_atencion")
    serializer_class = AtencionSerializer
    modulo = "cases"


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


class RecuperarPasswordView(APIView):
    permission_classes = []

    @extend_schema(request=RecuperarSerializer, responses=DetalleSerializer)
    def post(self, request):
        serializer = RecuperarSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        otp.solicitar(serializer.validated_data["email"])
        return Response({"detail": "Si el correo existe, se envió un código."})


class ValidarCodigoView(APIView):
    permission_classes = []

    @extend_schema(request=ValidarSerializer, responses=DetalleSerializer)
    def post(self, request):
        serializer = ValidarSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        datos = serializer.validated_data
        errores = otp.verificar(datos["email"], datos["code"])
        if errores:
            return Response({"detail": errores}, status=400)
        return Response({"detail": "Código válido."})


class NuevaPasswordView(APIView):
    permission_classes = []

    @extend_schema(request=NuevaPasswordSerializer, responses=DetalleSerializer)
    def post(self, request):
        serializer = NuevaPasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        datos = serializer.validated_data
        errores = otp.restablecer(datos["email"], datos["password"], datos["code"])
        if errores:
            return Response({"detail": errores}, status=400)
        return Response({"detail": "Contraseña actualizada."})
