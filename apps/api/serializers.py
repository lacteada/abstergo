"""Serializers de la API `v1`.

El contrato público está en inglés y el dominio interno sigue en español: cada
campo declara su `source` y conserva los validadores del modelo. Así el esquema
OpenAPI —que es lo que consume el cliente— también queda en inglés.
El glosario está en `documentacion/documento_tecnico.md`.
"""

from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import serializers

from apps.atenciones.models import Atencion
from apps.casos.models import CasoSocial
from apps.catalogos.models import FORMAS, SubAtencion, TipoAtencion
from apps.catalogos.models import Meta as MetaModel
from apps.ciudadanos.models import Vecino
from apps.common.estados import ESTADOS as ESTADOS_VIGENCIA
from apps.common.permisos import cargo_de, codigo_de, modulos_de
from apps.common.validators import (
    validar_catalogo,
    validar_codigo,
    validar_comuna,
    validar_direccion,
    validar_nombre,
    validar_rut,
    validar_telefono,
    validar_texto,
)
from apps.comunidad.models import Organizacion
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
from apps.sgr.validaciones import falta_evidencia
from apps.tubo.models import TareaTubo

Usuario = get_user_model()


class CodigoVisibleMixin(serializers.Serializer):
    """Expone la `referencia` del modelo con el nombre del contrato.

    Es el código que ve el usuario (`DEL-01`, `AT-01`…). Va como solo lectura:
    lo genera el servidor y no se puede fijar desde el cliente.
    """

    reference_code = serializers.CharField(source="referencia", read_only=True)


class LimpiaModeloMixin:
    """Corre el `clean()` del modelo al validar, como hace un ModelForm.

    DRF copia los validadores de campo del modelo, pero no ejecuta la validación
    de cruce de campos (`Model.clean()`). Este mixin la repone, para que la regla
    viva una sola vez —en el modelo— y la API no la salte. Va antes del
    `ModelSerializer` en la clase.
    """

    def validate(self, datos):
        datos = super().validate(datos)
        self.Meta.model(**datos).clean()
        return datos


class RolSerializer(CodigoVisibleMixin, serializers.ModelSerializer):
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
        fields = ["id", "reference_code", "code", "name", "description"]


class CargoSerializer(CodigoVisibleMixin, serializers.ModelSerializer):
    code = serializers.CharField(
        source="codigo",
        max_length=40,
        allow_null=True,
        required=False,
        validators=[validar_codigo],
    )
    name = serializers.CharField(source="nombre", max_length=80, validators=[validar_nombre])
    description = serializers.CharField(
        source="descripcion",
        max_length=200,
        allow_blank=True,
        required=False,
        validators=[validar_catalogo],
    )
    functions = serializers.CharField(
        source="funciones", allow_blank=True, required=False
    )

    class Meta:
        model = Cargo
        fields = ["id", "reference_code", "code", "name", "description", "functions"]


class UsuarioSerializer(CodigoVisibleMixin, serializers.ModelSerializer):
    role = serializers.PrimaryKeyRelatedField(
        source="rol", queryset=Rol.objects.all(), allow_null=True, required=False
    )
    position = serializers.PrimaryKeyRelatedField(
        source="cargo", queryset=Cargo.objects.all(), allow_null=True, required=False
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
            "reference_code",
            "email",
            "first_name",
            "last_name",
            "role",
            "position",
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
    position_code = serializers.SerializerMethodField()
    read_modules = serializers.SerializerMethodField()
    write_modules = serializers.SerializerMethodField()

    class Meta(UsuarioSerializer.Meta):
        fields = UsuarioSerializer.Meta.fields + [
            "role_code",
            "position_code",
            "read_modules",
            "write_modules",
        ]

    def get_role_code(self, obj) -> str | None:
        return codigo_de(obj)

    def get_position_code(self, obj) -> str | None:
        return cargo_de(obj)

    def get_read_modules(self, obj) -> list[str]:
        return sorted(modulos_de(obj))

    def get_write_modules(self, obj) -> list[str]:
        return sorted(modulos_de(obj, escritura=True))


class DelegacionSerializer(CodigoVisibleMixin, serializers.ModelSerializer):
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
        fields = ["id", "reference_code", "code", "name", "address", "commune", "manager"]


class TerritorioSerializer(CodigoVisibleMixin, serializers.ModelSerializer):
    name = serializers.CharField(source="nombre", max_length=120, validators=[validar_nombre])
    delegation = serializers.PrimaryKeyRelatedField(
        source="delegacion", queryset=Delegacion.objects.all()
    )
    status = serializers.ChoiceField(source="estado", choices=ESTADOS_VIGENCIA)

    class Meta:
        model = Territorio
        fields = ["id", "reference_code", "name", "delegation", "status"]


class MetaSerializer(CodigoVisibleMixin, serializers.ModelSerializer):
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
        fields = ["id", "reference_code", "name", "description", "delegation"]


class TipoAtencionSerializer(CodigoVisibleMixin, serializers.ModelSerializer):
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
        fields = ["id", "reference_code", "name", "description"]


class SubAtencionSerializer(CodigoVisibleMixin, serializers.ModelSerializer):
    name = serializers.CharField(source="nombre", max_length=120, validators=[validar_nombre])
    attention_type = serializers.PrimaryKeyRelatedField(
        source="tipo_atencion", queryset=TipoAtencion.objects.all()
    )
    form = serializers.ChoiceField(
        source="forma", choices=FORMAS, allow_blank=True, required=False
    )

    class Meta:
        model = SubAtencion
        fields = ["id", "reference_code", "name", "attention_type", "form"]


class VecinoSerializer(CodigoVisibleMixin, serializers.ModelSerializer):
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
            "reference_code",
            "name",
            "rut",
            "address",
            "phone",
            "territory",
            "management_type",
            "status",
        ]


class AtencionSerializer(CodigoVisibleMixin, LimpiaModeloMixin, serializers.ModelSerializer):
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
            "reference_code",
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


class OrganizacionSerializer(CodigoVisibleMixin, LimpiaModeloMixin, serializers.ModelSerializer):
    name = serializers.CharField(source="nombre", max_length=200, validators=[validar_texto])
    legal_address = serializers.CharField(
        source="domicilio_legal",
        max_length=200,
        allow_blank=True,
        required=False,
        validators=[validar_direccion],
    )
    territory = serializers.PrimaryKeyRelatedField(
        source="territorio",
        queryset=Delegacion.objects.all(),
        allow_null=True,
        required=False,
    )
    organization_type = serializers.ChoiceField(
        source="tipo",
        choices=Organizacion._meta.get_field("tipo").choices,
        allow_blank=True,
        required=False,
    )
    subtype = serializers.ChoiceField(
        source="subtipo",
        choices=Organizacion._meta.get_field("subtipo").choices,
        allow_blank=True,
        required=False,
    )
    situation = serializers.ChoiceField(
        source="situacion", choices=Organizacion._meta.get_field("situacion").choices
    )
    verification = serializers.ChoiceField(
        source="verificacion", choices=Organizacion._meta.get_field("verificacion").choices
    )
    active_members = serializers.IntegerField(
        source="socios_activos", allow_null=True, required=False, min_value=0
    )
    constitution_date = serializers.DateField(
        source="fecha_constitucion", allow_null=True, required=False
    )
    pj_registry = serializers.CharField(
        source="registro_pj",
        max_length=20,
        allow_blank=True,
        required=False,
        validators=[validar_catalogo],
    )
    registration_date = serializers.DateField(
        source="fecha_inscripcion", allow_null=True, required=False
    )
    directive_registry = serializers.CharField(
        source="registro_dir",
        max_length=20,
        allow_blank=True,
        required=False,
        validators=[validar_catalogo],
    )
    status = serializers.ChoiceField(source="estado", choices=ESTADOS_VIGENCIA)

    class Meta:
        model = Organizacion
        fields = [
            "id",
            "reference_code",
            "name",
            "legal_address",
            "territory",
            "organization_type",
            "subtype",
            "situation",
            "verification",
            "active_members",
            "constitution_date",
            "pj_registry",
            "registration_date",
            "directive_registry",
            "status",
        ]


class PeriodoSerializer(CodigoVisibleMixin, LimpiaModeloMixin, serializers.ModelSerializer):
    name = serializers.CharField(source="nombre", max_length=120, validators=[validar_catalogo])
    start = serializers.DateField(source="inicio")
    end = serializers.DateField(source="termino")
    days = serializers.IntegerField(source="dias", allow_null=True, required=False)
    situation = serializers.ChoiceField(
        source="situacion", choices=Periodo._meta.get_field("situacion").choices
    )
    min_threshold = serializers.DecimalField(
        source="umbral_minimo", max_digits=4, decimal_places=2
    )
    amber_threshold = serializers.DecimalField(
        source="umbral_ambar", max_digits=4, decimal_places=2
    )
    item_cap = serializers.DecimalField(
        source="tope_item", max_digits=4, decimal_places=2
    )
    total_cap = serializers.DecimalField(
        source="tope_total", max_digits=4, decimal_places=2
    )
    status = serializers.ChoiceField(source="estado", choices=ESTADOS_VIGENCIA)

    class Meta:
        model = Periodo
        fields = [
            "id",
            "reference_code",
            "name",
            "start",
            "end",
            "days",
            "situation",
            "min_threshold",
            "amber_threshold",
            "item_cap",
            "total_cap",
            "status",
        ]


class AreaSerializer(CodigoVisibleMixin, serializers.ModelSerializer):
    name = serializers.CharField(source="nombre", max_length=120, validators=[validar_catalogo])
    group = serializers.ChoiceField(source="grupo", choices=Area._meta.get_field("grupo").choices)
    position = serializers.PrimaryKeyRelatedField(
        source="cargo", queryset=Cargo.objects.all(), allow_null=True, required=False
    )
    manager = serializers.PrimaryKeyRelatedField(
        source="responsable", queryset=Usuario.objects.all(), allow_null=True, required=False
    )
    delegation = serializers.PrimaryKeyRelatedField(
        source="delegacion", queryset=Delegacion.objects.all(), allow_null=True, required=False
    )
    status = serializers.ChoiceField(source="estado", choices=ESTADOS_VIGENCIA)

    class Meta:
        model = Area
        fields = [
            "id",
            "reference_code",
            "name",
            "group",
            "position",
            "manager",
            "delegation",
            "status",
        ]


class IndicadorSerializer(CodigoVisibleMixin, serializers.ModelSerializer):
    name = serializers.CharField(source="nombre", max_length=200, validators=[validar_texto])
    group = serializers.ChoiceField(
        source="grupo", choices=Indicador._meta.get_field("grupo").choices
    )
    unit = serializers.ChoiceField(
        source="unidad", choices=Indicador._meta.get_field("unidad").choices
    )
    position = serializers.PrimaryKeyRelatedField(
        source="cargo", queryset=Cargo.objects.all(), allow_null=True, required=False
    )
    calculation_type = serializers.ChoiceField(
        source="tipo_calculo",
        choices=Indicador._meta.get_field("tipo_calculo").choices,
    )
    requires_evidence = serializers.BooleanField(source="requiere_evidencia")
    status = serializers.ChoiceField(source="estado", choices=ESTADOS_VIGENCIA)

    class Meta:
        model = Indicador
        fields = [
            "id",
            "reference_code",
            "name",
            "group",
            "unit",
            "position",
            "calculation_type",
            "requires_evidence",
            "status",
        ]


class MetaIndicadorSerializer(CodigoVisibleMixin, LimpiaModeloMixin, serializers.ModelSerializer):
    period = serializers.PrimaryKeyRelatedField(
        source="periodo", queryset=Periodo.objects.all()
    )
    area = serializers.PrimaryKeyRelatedField(queryset=Area.objects.all())
    indicator = serializers.PrimaryKeyRelatedField(
        source="indicador", queryset=Indicador.objects.all()
    )
    weight = serializers.DecimalField(source="ponderador", max_digits=6, decimal_places=3)
    target = serializers.DecimalField(source="meta", max_digits=10, decimal_places=2)
    staff = serializers.PrimaryKeyRelatedField(
        source="funcionario", queryset=Usuario.objects.all(), allow_null=True, required=False
    )
    effective_from = serializers.DateField(
        source="vigente_desde", allow_null=True, required=False
    )

    class Meta:
        model = MetaIndicador
        fields = [
            "id",
            "reference_code",
            "period",
            "area",
            "indicator",
            "weight",
            "target",
            "staff",
            "effective_from",
        ]


class RegistroGestionSerializer(CodigoVisibleMixin, serializers.ModelSerializer):
    date = serializers.DateField(source="fecha")
    area = serializers.PrimaryKeyRelatedField(queryset=Area.objects.all())
    indicator = serializers.PrimaryKeyRelatedField(
        source="indicador", queryset=Indicador.objects.all()
    )
    neighbor = serializers.PrimaryKeyRelatedField(
        source="vecino", queryset=Vecino.objects.all(), allow_null=True, required=False
    )
    commitment = serializers.PrimaryKeyRelatedField(
        source="compromiso", queryset=TareaTubo.objects.all(), allow_null=True, required=False
    )
    staff = serializers.PrimaryKeyRelatedField(
        source="funcionario", queryset=Usuario.objects.all()
    )
    quantity = serializers.IntegerField(source="cantidad", min_value=1)
    detail = serializers.CharField(source="detalle", allow_blank=True, required=False)
    stage = serializers.ChoiceField(
        source="etapa", choices=RegistroGestion._meta.get_field("etapa").choices
    )
    requester_type = serializers.ChoiceField(
        source="tipo_solicitante",
        choices=RegistroGestion._meta.get_field("tipo_solicitante").choices,
    )
    contact_name = serializers.CharField(
        source="contacto_nombre", allow_blank=True, required=False
    )
    contact_phone = serializers.CharField(
        source="contacto_telefono",
        allow_blank=True,
        required=False,
        validators=[validar_telefono],
    )
    scores = serializers.BooleanField(source="puntua", read_only=True)
    no_score_reason = serializers.CharField(source="motivo_no_puntua", read_only=True)
    status = serializers.ChoiceField(
        source="estado", choices=RegistroGestion._meta.get_field("estado").choices
    )
    action = serializers.CharField(
        source="accion", allow_blank=True, required=False
    )
    activity = serializers.ChoiceField(
        source="actividad",
        choices=RegistroGestion._meta.get_field("actividad").choices,
        allow_blank=True,
        required=False,
    )
    organization = serializers.PrimaryKeyRelatedField(
        source="organizacion",
        queryset=Organizacion.objects.all(),
        allow_null=True,
        required=False,
    )
    version = serializers.IntegerField(read_only=True)

    # Evidencia adjunta en la misma creación (una por actividad): se crea la
    # Evidencia al guardar el registro. Campos de escritura, no del modelo.
    evidence_file = serializers.FileField(
        source="evidencia_archivo", write_only=True, required=False
    )
    evidence_link = serializers.URLField(
        source="evidencia_vinculo", write_only=True, required=False, allow_blank=True
    )
    evidence_kind = serializers.CharField(
        source="evidencia_tipo", write_only=True, required=False, allow_blank=True
    )

    class Meta:
        model = RegistroGestion
        fields = [
            "id",
            "reference_code",
            "date",
            "area",
            "indicator",
            "neighbor",
            "staff",
            "quantity",
            "detail",
            "stage",
            "requester_type",
            "contact_name",
            "contact_phone",
            "scores",
            "no_score_reason",
            "status",
            "action",
            "activity",
            "organization",
            "commitment",
            "version",
            "evidence_file",
            "evidence_link",
            "evidence_kind",
        ]

    def validate(self, datos):
        # Se separa la evidencia de los datos del registro antes de validar.
        self._evidencia = {
            "archivo": datos.pop("evidencia_archivo", None),
            "vinculo": datos.pop("evidencia_vinculo", "") or "",
            "tipo": datos.pop("evidencia_tipo", "") or "",
        }
        # Igual que la web: la regla del 4° trimestre vive en el modelo.
        instancia = RegistroGestion(**{**datos})
        instancia.clean()
        # RN-010: la regla y su mensaje viven en un solo lugar (web y API).
        mensaje = falta_evidencia(
            datos.get("indicador"),
            self._evidencia["archivo"],
            self._evidencia["vinculo"],
        )
        if mensaje:
            raise serializers.ValidationError({"evidence_file": mensaje})
        archivo = self._evidencia["archivo"]
        if archivo:
            prueba = Evidencia(archivo=archivo)
            try:
                prueba.clean()
            except DjangoValidationError as error:
                raise serializers.ValidationError({"evidence_file": error.messages})
        return datos

    def create(self, validado):
        datos_evidencia = self._evidencia
        registro = RegistroGestion.objects.create(**validado)
        if datos_evidencia["archivo"] or datos_evidencia["vinculo"]:
            request = self.context.get("request")
            autor = getattr(request, "user", None) if request else None
            archivo = datos_evidencia["archivo"]
            Evidencia.objects.create(
                registro=registro,
                autor=autor,
                archivo=archivo,
                vinculo=datos_evidencia["vinculo"],
                tipo=datos_evidencia["tipo"],
                tamano=archivo.size if archivo else None,
            )
        return registro


class AjusteConductaSerializer(CodigoVisibleMixin, LimpiaModeloMixin, serializers.ModelSerializer):
    area = serializers.PrimaryKeyRelatedField(queryset=Area.objects.all())
    kind = serializers.ChoiceField(
        source="tipo", choices=AjusteConducta._meta.get_field("tipo").choices
    )
    date = serializers.DateField(source="fecha")
    backing = serializers.CharField(
        source="respaldo",
        max_length=200,
        allow_blank=True,
        required=False,
        validators=[validar_texto],
    )
    medium = serializers.ChoiceField(
        source="medio",
        choices=AjusteConducta._meta.get_field("medio").choices,
        allow_blank=True,
        required=False,
    )
    value = serializers.DecimalField(
        source="valor", max_digits=4, decimal_places=2, allow_null=True, required=False
    )
    period = serializers.PrimaryKeyRelatedField(
        source="periodo", queryset=Periodo.objects.all(), allow_null=True, required=False
    )

    class Meta:
        model = AjusteConducta
        fields = [
            "id",
            "reference_code",
            "area",
            "kind",
            "date",
            "backing",
            "medium",
            "value",
            "period",
        ]


class AusenciaSerializer(CodigoVisibleMixin, serializers.ModelSerializer):
    area = serializers.PrimaryKeyRelatedField(queryset=Area.objects.all())
    period = serializers.PrimaryKeyRelatedField(
        source="periodo", queryset=Periodo.objects.all(), allow_null=True, required=False
    )
    kind = serializers.ChoiceField(
        source="tipo", choices=Ausencia._meta.get_field("tipo").choices
    )
    start = serializers.DateField(source="desde")
    end = serializers.DateField(source="hasta")
    days = serializers.IntegerField(source="dias", read_only=True)

    class Meta:
        model = Ausencia
        fields = [
            "id",
            "reference_code",
            "area",
            "period",
            "kind",
            "start",
            "end",
            "days",
        ]


class EvidenciaSerializer(CodigoVisibleMixin, serializers.ModelSerializer):
    record = serializers.PrimaryKeyRelatedField(
        source="registro", queryset=RegistroGestion.objects.all()
    )
    file = serializers.FileField(source="archivo", required=False)
    link = serializers.URLField(source="vinculo", allow_blank=True, required=False)
    author = serializers.PrimaryKeyRelatedField(
        source="autor", queryset=Usuario.objects.all()
    )
    kind = serializers.CharField(source="tipo", allow_blank=True, required=False)
    review_status = serializers.ChoiceField(
        source="estado_revision", choices=Evidencia.REVISIONES, read_only=True
    )

    class Meta:
        model = Evidencia
        fields = [
            "id",
            "reference_code",
            "record",
            "file",
            "link",
            "author",
            "kind",
            "review_status",
        ]

    def validate(self, datos):
        # Aplica la misma regla del modelo (archivo obligatorio, formato y
        # tamaño), que el ModelSerializer no ejecuta por sí solo.
        instancia = Evidencia(**{**datos})
        instancia.clean()
        return datos


class ValidacionSerializer(CodigoVisibleMixin, LimpiaModeloMixin, serializers.ModelSerializer):
    evidence = serializers.PrimaryKeyRelatedField(
        source="evidencia", queryset=Evidencia.objects.all()
    )
    reviewer = serializers.PrimaryKeyRelatedField(
        source="verificador", queryset=Usuario.objects.all()
    )
    decision = serializers.ChoiceField(choices=Validacion.DECISIONES)
    observation = serializers.CharField(
        source="observacion", allow_blank=True, required=False
    )
    date = serializers.DateTimeField(source="fecha", read_only=True)

    class Meta:
        model = Validacion
        fields = [
            "id",
            "reference_code",
            "evidence",
            "reviewer",
            "decision",
            "observation",
            "date",
        ]


class TareaTuboSerializer(CodigoVisibleMixin, LimpiaModeloMixin, serializers.ModelSerializer):
    title = serializers.CharField(source="titulo", max_length=160, validators=[validar_texto])
    description = serializers.CharField(
        source="descripcion", allow_blank=True, required=False
    )
    status = serializers.ChoiceField(
        source="estado", choices=TareaTubo._meta.get_field("estado").choices
    )
    delegation = serializers.PrimaryKeyRelatedField(
        source="delegacion", queryset=Delegacion.objects.all()
    )
    assignee = serializers.PrimaryKeyRelatedField(
        source="responsable", queryset=Usuario.objects.all(), allow_null=True, required=False
    )
    neighbor = serializers.PrimaryKeyRelatedField(
        source="vecino", queryset=Vecino.objects.all(), allow_null=True, required=False
    )
    created_at = serializers.DateTimeField(source="fecha_ingreso", read_only=True)
    due_date = serializers.DateField(
        source="fecha_compromiso", allow_null=True, required=False
    )
    territory = serializers.PrimaryKeyRelatedField(
        source="territorio", queryset=Territorio.objects.all(), allow_null=True, required=False
    )
    kind = serializers.ChoiceField(
        source="tipo", choices=TareaTubo._meta.get_field("tipo").choices
    )
    requester = serializers.CharField(
        source="solicitante", max_length=160, allow_blank=True, required=False
    )
    support = serializers.PrimaryKeyRelatedField(
        source="apoyo", queryset=Usuario.objects.all(), allow_null=True, required=False
    )
    progress = serializers.IntegerField(
        source="avance", min_value=0, max_value=100, required=False
    )
    overdue = serializers.BooleanField(source="vencida", read_only=True)

    class Meta:
        model = TareaTubo
        fields = [
            "id",
            "reference_code",
            "title",
            "description",
            "status",
            "delegation",
            "territory",
            "kind",
            "requester",
            "assignee",
            "support",
            "neighbor",
            "progress",
            "overdue",
            "created_at",
            "due_date",
        ]


class CasoSocialSerializer(CodigoVisibleMixin, LimpiaModeloMixin, serializers.ModelSerializer):
    neighbor = serializers.PrimaryKeyRelatedField(
        source="vecino", queryset=Vecino.objects.all()
    )
    manager = serializers.PrimaryKeyRelatedField(
        source="responsable", queryset=Usuario.objects.all(), allow_null=True, required=False
    )
    opened_at = serializers.DateField(source="fecha_apertura")
    reason = serializers.CharField(source="motivo", max_length=200, validators=[validar_texto])
    status = serializers.ChoiceField(
        source="estado", choices=CasoSocial._meta.get_field("estado").choices
    )
    is_reentry = serializers.BooleanField(source="reingreso", required=False)
    previous_case = serializers.PrimaryKeyRelatedField(
        source="caso_anterior",
        queryset=CasoSocial.objects.all(),
        allow_null=True,
        required=False,
    )
    notes = serializers.CharField(source="observaciones", allow_blank=True, required=False)

    class Meta:
        model = CasoSocial
        fields = [
            "id",
            "reference_code",
            "neighbor",
            "manager",
            "opened_at",
            "reason",
            "status",
            "is_reentry",
            "previous_case",
            "notes",
        ]


class ComentarioSerializer(CodigoVisibleMixin, serializers.ModelSerializer):
    record = serializers.PrimaryKeyRelatedField(
        source="registro", queryset=RegistroGestion.objects.all()
    )
    author = serializers.PrimaryKeyRelatedField(
        source="autor", queryset=Usuario.objects.all()
    )
    text = serializers.CharField(source="texto")
    date = serializers.DateTimeField(source="fecha", read_only=True)

    class Meta:
        model = Comentario
        fields = ["id", "reference_code", "record", "author", "text", "date"]


class AlertaSerializer(CodigoVisibleMixin, serializers.ModelSerializer):
    kind = serializers.ChoiceField(source="tipo", choices=Alerta.TIPOS)
    severity = serializers.ChoiceField(source="severidad", choices=Alerta.SEVERIDADES)
    message = serializers.CharField(
        source="mensaje", max_length=200, validators=[validar_texto]
    )
    area = serializers.PrimaryKeyRelatedField(
        queryset=Area.objects.all(), allow_null=True, required=False
    )
    solved = serializers.BooleanField(source="resuelta", required=False)
    date = serializers.DateTimeField(source="fecha", read_only=True)

    class Meta:
        model = Alerta
        fields = ["id", "reference_code", "kind", "severity", "message", "area", "solved", "date"]


class DetalleSerializer(serializers.Serializer):
    """Respuesta simple con un mensaje."""

    detail = serializers.CharField()


class RegistroSerializer(serializers.Serializer):
    """El alta pública: el correo es el identificador y no puede repetirse.

    Nombre y apellido son obligatorios y pasan por `validar_nombre`, la misma
    regla de los mantenedores: no se crean cuentas sin titular ni con números.
    """

    email = serializers.EmailField()
    first_name = serializers.CharField(max_length=60, validators=[validar_nombre])
    last_name = serializers.CharField(max_length=60, validators=[validar_nombre])
    password = serializers.CharField(write_only=True)

    def validate_email(self, valor):
        # Se guarda en minúsculas: el correo es la llave de entrada y el login
        # es sensible a mayúsculas.
        correo = valor.strip().lower()
        if Usuario.vigentes().filter(email__iexact=correo).exists():
            raise serializers.ValidationError("Ese correo ya está registrado.")
        return correo

    def validate_password(self, valor):
        validate_password(valor)
        return valor

    def create(self, validated_data):
        return Usuario.objects.create_user(
            email=validated_data["email"],
            password=validated_data["password"],
            first_name=validated_data["first_name"],
            last_name=validated_data["last_name"],
        )


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

    def validate_password(self, valor):
        # La misma regla que el registro y la web, para no aceptar claves débiles.
        validate_password(valor)
        return valor
