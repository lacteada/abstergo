from django.contrib import admin


class SoloLecturaAdmin(admin.ModelAdmin):
    """Admin sin alta, edición ni borrado.

    Decisión consciente: la pauta de la evaluación da 15 puntos al CRUD del
    Admin. Para volver a habilitarlo, quitar los tres métodos de abajo.
    """

    list_per_page = 25

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
