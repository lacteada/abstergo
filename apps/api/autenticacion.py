"""MFA también en JWT y sesiones de API; un endpoint alternativo no elude el factor."""

from django.contrib.auth import authenticate, get_user_model
from rest_framework import serializers
from rest_framework.authentication import SessionAuthentication
from rest_framework.exceptions import AuthenticationFailed
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer, TokenRefreshSerializer
from rest_framework_simplejwt.settings import api_settings
from rest_framework_simplejwt.utils import get_md5_hash_password

from apps.cuentas import mfa


def comprobar_version(usuario, token):
    if token.get("mfa_version", 0) != mfa.version(usuario):
        raise AuthenticationFailed("Credencial revocada. Inicia sesión nuevamente.")


class JWTConSegundoFactor(JWTAuthentication):
    def get_user(self, validated_token):
        usuario = super().get_user(validated_token)
        comprobar_version(usuario, validated_token)
        return usuario


class SesionConSegundoFactor(SessionAuthentication):
    def authenticate(self, request):
        resultado = super().authenticate(request)
        if resultado:
            comprobar_version(resultado[0], request.session)
        return resultado


class TokenConSegundoFactor(TokenObtainPairSerializer):
    otp = serializers.CharField(required=False, write_only=True, max_length=32)

    def validate(self, attrs):
        usuario = authenticate(
            request=self.context.get("request"),
            email=attrs.get("email"),
            password=attrs.get("password"),
        )
        if usuario and usuario.is_active and usuario.eliminado is None:
            factor = mfa.credencial(usuario)
            if factor and factor.activo:
                if not attrs.get("otp"):
                    raise AuthenticationFailed("Segundo factor requerido.", code="mfa_required")
                if not mfa.verificar(usuario, attrs["otp"]):
                    raise AuthenticationFailed(mfa.ERROR_CODIGO)
        elif usuario and usuario.eliminado is not None:
            raise AuthenticationFailed("Credenciales inválidas.")
        return super().validate(attrs)

    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token["mfa_version"] = mfa.version(user)
        return token


class RenovarConSegundoFactor(TokenRefreshSerializer):
    def validate(self, attrs):
        token = self.token_class(attrs["refresh"])
        usuario = (
            get_user_model()
            .objects.filter(
                pk=token.get("user_id"),
                is_active=True,
                eliminado__isnull=True,
            )
            .first()
        )
        if not usuario:
            raise AuthenticationFailed("Credencial revocada.")
        if api_settings.CHECK_REVOKE_TOKEN and token.get(
            api_settings.REVOKE_TOKEN_CLAIM
        ) != get_md5_hash_password(usuario.password):
            raise AuthenticationFailed("Contraseña cambiada. Inicia sesión nuevamente.")
        comprobar_version(usuario, token)
        return super().validate(attrs)
