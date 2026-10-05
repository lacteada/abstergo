"""Normaliza el RUT guardado y corrige el dígito verificador.

Mantiene la misma base de cada vecino, así que no cambia de persona. Los RUT
cargados antes traían puntos y algunos un DV equivocado; el mantenedor ahora
valida el DV, así que hay que dejarlos consistentes.
"""

import re

from django.db import migrations


def _digito_verificador(cuerpo):
    suma = 0
    multiplicador = 2
    for digito in reversed(cuerpo):
        suma += int(digito) * multiplicador
        multiplicador = multiplicador + 1 if multiplicador < 7 else 2
    resto = 11 - (suma % 11)
    return {10: "K", 11: "0"}.get(resto, str(resto))


def normalizar_rut(apps, schema_editor):
    Vecino = apps.get_model("ciudadanos", "Vecino")
    for vecino in Vecino.objects.all():
        limpio = re.sub(r"[.\s]", "", vecino.rut or "").upper()
        cuerpo = limpio.split("-")[0] if "-" in limpio else limpio[:-1]
        if not cuerpo.isdigit():
            continue
        rut = f"{cuerpo}-{_digito_verificador(cuerpo)}"
        if rut != vecino.rut:
            vecino.rut = rut
            vecino.save(update_fields=["rut"])


class Migration(migrations.Migration):

    dependencies = [
        ("ciudadanos", "0002_alter_vecino_direccion_alter_vecino_nombre_and_more"),
    ]

    operations = [
        migrations.RunPython(normalizar_rut, migrations.RunPython.noop),
    ]
