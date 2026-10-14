"""Serializers de la API `v1`."""

from django.contrib.auth import get_user_model
from rest_framework import serializers

from apps.atenciones.models import Atencion
from apps.catalogos.models import Meta as MetaModel
from apps.catalogos.models import SubAtencion, TipoAtencion
from apps.ciudadanos.models import Vecino
from apps.common.permisos import codigo_de, modulos_de
from apps.cuentas.models import Rol
from apps.organizacion.models import Delegacion

Usuario = get_user_model()


class RolSerializer(serializers.ModelSerializer):
    class Meta:
        model = Rol
        fields = ["id", "codigo", "nombre", "descripcion"]


class UsuarioSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=False, allow_blank=True)

    class Meta:
        model = Usuario
        fields = [
            "id",
            "email",
            "first_name",
            "last_name",
            "rol",
            "delegacion",
            "is_active",
            "password",
        ]

    def create(self, validated_data):
        password = validated_data.pop("password", "") or None
        usuario = Usuario(**validated_data)
        if password:
            usuario.set_password(password)
        else:
            usuario.set_unusable_password()
        usuario.save()
        return usuario

    def update(self, instance, validated_data):
        password = validated_data.pop("password", "")
        for campo, valor in validated_data.items():
            setattr(instance, campo, valor)
        if password:
            instance.set_password(password)
        instance.save()
        return instance


class PerfilSerializer(UsuarioSerializer):
    """El usuario más lo que puede hacer, para que el cliente no repita la matriz."""

    rol_codigo = serializers.SerializerMethodField()
    modulos_lectura = serializers.SerializerMethodField()
    modulos_escritura = serializers.SerializerMethodField()

    class Meta(UsuarioSerializer.Meta):
        fields = UsuarioSerializer.Meta.fields + [
            "rol_codigo",
            "modulos_lectura",
            "modulos_escritura",
        ]

    def get_rol_codigo(self, obj):
        return codigo_de(obj)

    def get_modulos_lectura(self, obj):
        return sorted(modulos_de(obj))

    def get_modulos_escritura(self, obj):
        return sorted(modulos_de(obj, escritura=True))


class DelegacionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Delegacion
        fields = ["id", "codigo", "nombre", "direccion", "comuna", "responsable"]


class MetaSerializer(serializers.ModelSerializer):
    class Meta:
        model = MetaModel
        fields = ["id", "nombre", "descripcion", "delegacion"]


class TipoAtencionSerializer(serializers.ModelSerializer):
    class Meta:
        model = TipoAtencion
        fields = ["id", "nombre", "descripcion"]


class SubAtencionSerializer(serializers.ModelSerializer):
    class Meta:
        model = SubAtencion
        fields = ["id", "nombre", "tipo_atencion"]


class VecinoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Vecino
        fields = [
            "id",
            "nombre",
            "rut",
            "direccion",
            "telefono",
            "territorio",
            "tipo_gestion",
            "estado",
        ]


class AtencionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Atencion
        fields = [
            "id",
            "vecino",
            "tipo_atencion",
            "sub_atencion",
            "delegacion",
            "funcionario",
            "fecha",
            "motivo",
            "detalle",
            "estado",
            "canal",
        ]
        read_only_fields = ["fecha"]


class DetalleSerializer(serializers.Serializer):
    """Respuesta simple con un mensaje."""

    detail = serializers.CharField()


class LogoutSerializer(serializers.Serializer):
    refresh = serializers.CharField()


class RecuperarSerializer(serializers.Serializer):
    email = serializers.EmailField()


class ValidarSerializer(serializers.Serializer):
    email = serializers.EmailField()
    codigo = serializers.CharField(max_length=6)


class NuevaPasswordSerializer(serializers.Serializer):
    email = serializers.EmailField()
    codigo = serializers.CharField(max_length=6)
    password = serializers.CharField(write_only=True)
