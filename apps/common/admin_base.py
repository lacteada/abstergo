from django.contrib import admin


class AdminBase(admin.ModelAdmin):
    """Admin con CRUD y borrado normal.

    Las 7 entidades heredan de aquí, así que el alta, la edición y el borrado
    se habilitan una sola vez. El borrado del Admin emite DELETE de verdad (a
    diferencia del front, que usa borrado lógico): las llaves foráneas en
    PROTECT impiden borrar una fila que otra siga referenciando.
    """

    list_per_page = 25
