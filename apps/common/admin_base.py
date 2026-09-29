from django.contrib import admin
from django.utils import timezone


class AdminBase(admin.ModelAdmin):
    """Admin con CRUD y borrado lógico.

    Las 7 entidades heredan de aquí, así que el alta, la edición y el borrado
    se habilitan una sola vez. El borrado respeta la regla del proyecto: no se
    emite DELETE, la fila se marca con `eliminado` para que quien la referencie
    conserve el vínculo.
    """

    list_per_page = 25

    def delete_model(self, request, obj):
        obj.eliminar()

    def delete_queryset(self, request, queryset):
        queryset.update(eliminado=timezone.now())
