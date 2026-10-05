"""Rellena el código de los roles que existían antes del campo.

El código es estable y lo usa el dashboard para ramificar por rol. Los roles
ya cargados no lo tenían; se deriva del nombre para no duplicar al recargar
datos_nuevos/roles.json (que ahora se indexa por código).
"""

from django.db import migrations
from django.utils.text import slugify


def rellenar_codigo(apps, schema_editor):
    Rol = apps.get_model("cuentas", "Rol")
    for rol in Rol.objects.filter(codigo__isnull=True):
        codigo = slugify(rol.nombre)[:40]
        if codigo and not Rol.objects.filter(codigo=codigo).exists():
            rol.codigo = codigo
            rol.save(update_fields=["codigo"])


class Migration(migrations.Migration):

    dependencies = [
        ("cuentas", "0002_rol_codigo_alter_rol_descripcion_alter_rol_nombre"),
    ]

    operations = [
        migrations.RunPython(rellenar_codigo, migrations.RunPython.noop),
    ]
