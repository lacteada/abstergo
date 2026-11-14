"""Vistas de la API `v1`: CRUD con borrado lógico, autenticación y recuperación."""

from django.contrib.auth import get_user_model
from drf_spectacular.utils import extend_schema
from rest_framework import status, viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

from apps.atenciones.models import Atencion
from apps.casos.models import CasoSocial, GestionCaso, Llamada
from apps.catalogos.models import Meta as MetaModel
from apps.catalogos.models import SubAtencion, TipoAtencion
from apps.ciudadanos.models import Vecino
from apps.comunidad.models import Organizacion
from apps.cuentas import otp
from apps.cuentas.models import Rol
from apps.organizacion.models import Cargo, Delegacion, Territorio
from apps.sgr.models import (
    AjusteConducta,
    Alerta,
    Area,
    Ausencia,
    Comentario,
    Evidencia,
    Indicador,
    MetaIndicador,
    Periodo,
    RegistroGestion,
    Validacion,
)
from apps.tubo.models import Carta, TareaTubo

from .permissions import PermisoPorRol
from .serializers import (
    AjusteConductaSerializer,
    AlertaSerializer,
    AreaSerializer,
    AtencionSerializer,
    AusenciaSerializer,
    CargoSerializer,
    CartaSerializer,
    CasoSocialSerializer,
    ComentarioSerializer,
    DelegacionSerializer,
    DetalleSerializer,
    EvidenciaSerializer,
    GestionCasoSerializer,
    IndicadorSerializer,
    LlamadaSerializer,
    LogoutSerializer,
    MetaIndicadorSerializer,
    MetaSerializer,
    NuevaPasswordSerializer,
    OrganizacionSerializer,
    PerfilSerializer,
    PeriodoSerializer,
    RecuperarSerializer,
    RegistroGestionSerializer,
    RegistroSerializer,
    RolSerializer,
    SubAtencionSerializer,
    TareaTuboSerializer,
    TerritorioSerializer,
    TipoAtencionSerializer,
    UsuarioSerializer,
    ValidacionSerializer,
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


class CargoViewSet(BaseViewSet):
    queryset = Cargo.objects.all()
    serializer_class = CargoSerializer
    modulo = "positions"


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


class TerritorioViewSet(BaseViewSet):
    queryset = Territorio.objects.select_related("delegacion")
    serializer_class = TerritorioSerializer
    modulo = "territories"


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


class OrganizacionViewSet(BaseViewSet):
    queryset = Organizacion.objects.select_related("territorio")
    serializer_class = OrganizacionSerializer
    modulo = "community"


class PeriodoViewSet(BaseViewSet):
    queryset = Periodo.objects.all()
    serializer_class = PeriodoSerializer
    modulo = "sgr"


class AreaViewSet(BaseViewSet):
    queryset = Area.objects.select_related("cargo", "responsable", "delegacion")
    serializer_class = AreaSerializer
    modulo = "sgr"


class IndicadorViewSet(BaseViewSet):
    queryset = Indicador.objects.all()
    serializer_class = IndicadorSerializer
    modulo = "sgr"


class MetaIndicadorViewSet(BaseViewSet):
    queryset = MetaIndicador.objects.select_related("periodo", "area", "indicador")
    serializer_class = MetaIndicadorSerializer
    modulo = "sgr"


class RegistroGestionViewSet(BaseViewSet):
    queryset = RegistroGestion.objects.select_related("area", "indicador", "vecino")
    serializer_class = RegistroGestionSerializer
    modulo = "sgr_records"


class AjusteConductaViewSet(BaseViewSet):
    queryset = AjusteConducta.objects.select_related("area", "periodo")
    serializer_class = AjusteConductaSerializer
    modulo = "sgr_adjustments"


class AusenciaViewSet(BaseViewSet):
    queryset = Ausencia.objects.select_related("area", "periodo")
    serializer_class = AusenciaSerializer
    modulo = "sgr_adjustments"


class TareaTuboViewSet(BaseViewSet):
    queryset = TareaTubo.objects.select_related("delegacion", "responsable", "vecino")
    serializer_class = TareaTuboSerializer
    modulo = "tasks"


class CartaViewSet(BaseViewSet):
    queryset = Carta.objects.select_related("delegacion", "responsable")
    serializer_class = CartaSerializer
    modulo = "letters"


class CasoSocialViewSet(BaseViewSet):
    queryset = CasoSocial.objects.select_related("vecino", "responsable")
    serializer_class = CasoSocialSerializer
    modulo = "social_cases"


class GestionCasoViewSet(BaseViewSet):
    queryset = GestionCaso.objects.select_related("caso")
    serializer_class = GestionCasoSerializer
    modulo = "social_cases"


class LlamadaViewSet(BaseViewSet):
    queryset = Llamada.objects.select_related("vecino", "responsable")
    serializer_class = LlamadaSerializer
    modulo = "social_cases"


class ComentarioViewSet(BaseViewSet):
    queryset = Comentario.objects.select_related("registro", "autor")
    serializer_class = ComentarioSerializer
    modulo = "comments"


class AlertaViewSet(BaseViewSet):
    queryset = Alerta.objects.select_related("area")
    serializer_class = AlertaSerializer
    modulo = "alerts"


class EvidenciaViewSet(BaseViewSet):
    queryset = Evidencia.objects.select_related("registro", "autor")
    serializer_class = EvidenciaSerializer
    modulo = "evidence"


class ValidacionViewSet(BaseViewSet):
    queryset = Validacion.objects.select_related("evidencia", "verificador")
    serializer_class = ValidacionSerializer
    modulo = "validation"


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
        otp.solicitar(serializer.validated_data["email"], request)
        return Response({"detail": "Si el correo existe, se envió un código."})


class RegistroView(APIView):
    """Alta pública de usuario: el correo es el identificador."""

    permission_classes = []

    @extend_schema(request=RegistroSerializer, responses={201: UsuarioSerializer})
    def post(self, request):
        serializer = RegistroSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        usuario = serializer.save()
        return Response(UsuarioSerializer(usuario).data, status=status.HTTP_201_CREATED)


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
