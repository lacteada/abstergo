from django.contrib import admin

from apps.common.admin_base import AdminBase
from apps.cumplimiento.models import (
    ActividadTratamiento,
    Consentimiento,
    IncidenteSeguridad,
    RegistroAuditoria,
    SolicitudTitular,
)


@admin.register(ActividadTratamiento)
class ActividadTratamientoAdmin(AdminBase):
    list_display = ("nombre", "base_licitud", "plazo_conservacion_dias", "responsable")
    search_fields = ("nombre", "finalidad", "categorias_datos")
    list_filter = ("base_licitud",)
    autocomplete_fields = ("responsable",)


@admin.register(SolicitudTitular)
class SolicitudTitularAdmin(AdminBase):
    list_display = ("vecino", "tipo", "estado", "fecha_solicitud", "fecha_limite")
    search_fields = ("vecino__nombre", "vecino__rut", "detalle")
    list_filter = ("tipo", "estado")
    autocomplete_fields = ("vecino", "respondido_por")
    date_hierarchy = "fecha_solicitud"


@admin.register(IncidenteSeguridad)
class IncidenteSeguridadAdmin(AdminBase):
    list_display = ("fecha_deteccion", "gravedad", "notificado_apdp", "notificado_titulares")
    search_fields = ("descripcion", "datos_afectados")
    list_filter = ("gravedad", "notificado_apdp", "notificado_titulares")


@admin.register(RegistroAuditoria)
class RegistroAuditoriaAdmin(admin.ModelAdmin):
    list_display = ("fecha", "usuario", "accion", "tabla", "objeto_id", "ip")
    search_fields = ("tabla", "objeto_id", "detalle", "usuario__email")
    list_filter = ("accion",)
    date_hierarchy = "fecha"
    readonly_fields = (
        "usuario",
        "accion",
        "tabla",
        "objeto_id",
        "fecha",
        "ip",
        "detalle",
    )

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(Consentimiento)
class ConsentimientoAdmin(AdminBase):
    list_display = ("vecino", "actividad", "otorgado", "revocado", "fecha")
    search_fields = ("vecino__nombre", "vecino__rut", "actividad__nombre")
    list_filter = ("otorgado", "revocado")
    autocomplete_fields = ("vecino", "actividad")
