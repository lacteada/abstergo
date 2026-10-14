"""Serializers de la API `v1`.

El contrato público está en inglés y el dominio interno sigue en español: cada
campo declara su `source` y conserva los validadores del modelo. Así el esquema
OpenAPI —que es lo que consume el cliente— también queda en inglés.
El glosario está en `documentacion/documento_tecnico.md`.
"""

from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers

from apps.atenciones.models import Atencion
from apps.catalogos.models import Meta as MetaModel
from apps.catalogos.models import SubAtencion, TipoAtencion
from apps.ciudadanos.models import Vecino
from apps.common.permisos import codigo_de, modulos_de
from apps.common.validators import (
    validar_catalogo,
    validar_codigo,
    validar_comuna,
    validar_direccion,
    validar_nombre,
    validar_rut,
    validar_telefono,
)
from apps.cuentas.models import Rol
from apps.organizacion.models import Delegacion

Usuario = get_user_model()


class RolSerializer(serializers.ModelSerializer):
    code = serializers.CharField(
        source="codigo",
        max_length=40,
        allow_null=True,
        required=False,
        validators=[validar_codigo],
    )
    name = serializers.CharField(source="nombre", max_length=60, validators=[validar_nombre])
    description = serializers.CharField(
        source="descripcion",
        max_length=200,
        allow_blank=True,
        required=False,
        validators=[validar_catalogo],
    )

    class Meta:
        model = Rol
        fields = ["id", "code", "name", "description"]


class UsuarioSerializer(serializers.ModelSerializer):
    role = serializers.PrimaryKeyRelatedField(
        source="rol", queryset=Rol.objects.all(), allow_null=True, required=False
    )
    delegation = serializers.PrimaryKeyRelatedField(
        source="delegacion",
        queryset=Delegacion.objects.all(),
        allow_null=True,
        required=False,
    )
    password = serializers.CharField(write_only=True, required=False, allow_blank=True)

    class Meta:
        model = Usuario
        fields = [
            "id",
            "email",
            "first_name",
            "last_name",
            "role",
            "delegation",
            "is_active",
            "password",
        ]

    def validate_password(self, valor):
        # La misma regla para la web, la API y el Admin.
        if valor:
            validate_password(valor, self.instance)
        return valor

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

    role_code = serializers.SerializerMethodField()
    read_modules = serializers.SerializerMethodField()
    write_modules = serializers.SerializerMethodField()

    class Meta(UsuarioSerializer.Meta):
        fields = UsuarioSerializer.Meta.fields + [
            "role_code",
            "read_modules",
            "write_modules",
        ]

    def get_role_code(self, obj) -> str | None:
        return codigo_de(obj)

    def get_read_modules(self, obj) -> list[str]:
        return sorted(modulos_de(obj))

    def get_write_modules(self, obj) -> list[str]:
        return sorted(modulos_de(obj, escritura=True))


class DelegacionSerializer(serializers.ModelSerializer):
    code = serializers.CharField(
        source="codigo", max_length=40, validators=[validar_codigo]
    )
    name = serializers.CharField(source="nombre", max_length=120, validators=[validar_nombre])
    address = serializers.CharField(
        source="direccion",
        max_length=200,
        allow_blank=True,
        required=False,
        validators=[validar_direccion],
    )
    commune = serializers.CharField(
        source="comuna",
        max_length=80,
        allow_blank=True,
        required=False,
        validators=[validar_comuna],
    )
    manager = serializers.PrimaryKeyRelatedField(
        source="responsable",
        queryset=Usuario.objects.all(),
        allow_null=True,
        required=False,
    )

    class Meta:
        model = Delegacion
        fields = ["id", "code", "name", "address", "commune", "manager"]


class MetaSerializer(serializers.ModelSerializer):
    name = serializers.CharField(source="nombre", max_length=120, validators=[validar_nombre])
    description = serializers.CharField(
        source="descripcion",
        max_length=200,
        allow_blank=True,
        required=False,
        validators=[validar_catalogo],
    )
    delegation = serializers.PrimaryKeyRelatedField(
        source="delegacion", queryset=Delegacion.objects.all()
    )

    class Meta:
        model = MetaModel
        fields = ["id", "name", "description", "delegation"]


class TipoAtencionSerializer(serializers.ModelSerializer):
    name = serializers.CharField(source="nombre", max_length=120, validators=[validar_nombre])
    description = serializers.CharField(
        source="descripcion",
        max_length=200,
        allow_blank=True,
        required=False,
        validators=[validar_catalogo],
    )

    class Meta:
        model = TipoAtencion
        fields = ["id", "name", "description"]


class SubAtencionSerializer(serializers.ModelSerializer):
    name = serializers.CharField(source="nombre", max_length=120, validators=[validar_nombre])
    attention_type = serializers.PrimaryKeyRelatedField(
        source="tipo_atencion", queryset=TipoAtencion.objects.all()
    )

    class Meta:
        model = SubAtencion
        fields = ["id", "name", "attention_type"]


class VecinoSerializer(serializers.ModelSerializer):
    name = serializers.CharField(source="nombre", max_length=120, validators=[validar_nombre])
    rut = serializers.CharField(max_length=15, validators=[validar_rut])
    address = serializers.CharField(
        source="direccion",
        max_length=200,
        allow_blank=True,
        required=False,
        validators=[validar_direccion],
    )
    phone = serializers.CharField(
        source="telefono",
        max_length=30,
        allow_blank=True,
        required=False,
        validators=[validar_telefono],
    )
    territory = serializers.PrimaryKeyRelatedField(
        source="territorio", queryset=Delegacion.objects.all()
    )
    management_type = serializers.CharField(
        source="tipo_gestion",
        max_length=80,
        allow_blank=True,
        required=False,
        validators=[validar_catalogo],
    )
    status = serializers.ChoiceField(source="estado", choices=Vecino.ESTADOS)

    class Meta:
        model = Vecino
        fields = [
            "id",
            "name",
            "rut",
            "address",
            "phone",
            "territory",
            "management_type",
            "status",
        ]


class AtencionSerializer(serializers.ModelSerializer):
    neighbor = serializers.PrimaryKeyRelatedField(
        source="vecino", queryset=Vecino.objects.all()
    )
    attention_type = serializers.PrimaryKeyRelatedField(
        source="tipo_atencion", queryset=TipoAtencion.objects.all()
    )
    attention_subtype = serializers.PrimaryKeyRelatedField(
        source="sub_atencion",
        queryset=SubAtencion.objects.all(),
        allow_null=True,
        required=False,
    )
    delegation = serializers.PrimaryKeyRelatedField(
        source="delegacion", queryset=Delegacion.objects.all()
    )
    staff = serializers.PrimaryKeyRelatedField(
        source="funcionario", queryset=Usuario.objects.all()
    )
    date = serializers.DateTimeField(source="fecha", read_only=True)
    reason = serializers.CharField(source="motivo", max_length=200)
    detail = serializers.CharField(
        source="detalle", allow_blank=True, required=False
    )
    status = serializers.ChoiceField(source="estado", choices=Atencion.ESTADOS)
    channel = serializers.ChoiceField(
        source="canal", choices=Atencion.CANALES, allow_blank=True, required=False
    )

    class Meta:
        model = Atencion
        fields = [
            "id",
            "neighbor",
            "attention_type",
            "attention_subtype",
            "delegation",
            "staff",
            "date",
            "reason",
            "detail",
            "status",
            "channel",
        ]


class DetalleSerializer(serializers.Serializer):
    """Respuesta simple con un mensaje."""

    detail = serializers.CharField()


class LogoutSerializer(serializers.Serializer):
    refresh = serializers.CharField()


class RecuperarSerializer(serializers.Serializer):
    email = serializers.EmailField()


class ValidarSerializer(serializers.Serializer):
    email = serializers.EmailField()
    code = serializers.CharField(max_length=6, min_length=6)


class NuevaPasswordSerializer(serializers.Serializer):
    email = serializers.EmailField()
    code = serializers.CharField(max_length=6, min_length=6)
    password = serializers.CharField(write_only=True)
