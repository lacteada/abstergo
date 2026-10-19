"""Rellena el `codigo` de los catálogos ya cargados.

El campo nace nulo para no romper las filas existentes; acá se deriva del
nombre, que es la única llave que traían. Los nombres del JSON no traen tildes
en el slug (slugify las elimina), así que el resultado es estable.
"""

from django.db import migrations
from django.utils.text import slugify


def rellenar(apps, schema_editor):
    for nombre_modelo in ("Meta", "TipoAtencion", "SubAtencion"):
        modelo = apps.get_model("catalogos", nombre_modelo)
        for fila in modelo.objects.all():
            if fila.codigo:
                continue
            base = slugify(fila.nombre)[:40] or f"registro-{fila.pk}"
            codigo = base
            sufijo = 2
            while (
                modelo.objects.filter(codigo=codigo).exclude(pk=fila.pk).exists()
            ):
                codigo = f"{base[:36]}-{sufijo}"
                sufijo += 1
            fila.codigo = codigo
            fila.save(update_fields=["codigo"])


def vaciar(apps, schema_editor):
    for nombre_modelo in ("Meta", "TipoAtencion", "SubAtencion"):
        apps.get_model("catalogos", nombre_modelo).objects.update(codigo=None)


class Migration(migrations.Migration):
    dependencies = [
        ("catalogos", "0003_meta_codigo_meta_estado_subatencion_codigo_and_more"),
    ]

    operations = [migrations.RunPython(rellenar, vaciar)]
