# Directiva de la organización: de texto suelto a personas reales (Vecino).
#
# En MySQL no se puede convertir una columna CharField en ForeignKey de una
# pasada, así que se hace en tres tiempos: se renombra el texto, se agrega la
# llave foránea, se copia lo que se pueda emparejar y se borra el texto.

import django.db.models.deletion
from django.db import migrations, models


def copiar_directiva(apps, schema_editor):
    """Pasa el nombre de la directiva a la persona (Vecino) cuando coincide.

    Es best-effort: si no hay un vecino con ese nombre en la delegación, el
    cargo queda sin persona. La importación de JJVV dejó la directiva vacía, así
    que en la práctica no hay nada que copiar.
    """
    Organizacion = apps.get_model("comunidad", "Organizacion")
    Vecino = apps.get_model("ciudadanos", "Vecino")
    for organizacion in Organizacion.objects.all():
        for rol in ("presidente", "tesorero", "secretario"):
            texto = (getattr(organizacion, f"{rol}_texto") or "").strip()
            if not texto:
                continue
            candidatos = Vecino.objects.filter(territorio_id=organizacion.territorio_id)
            elegido = candidatos.filter(nombre__iexact=texto).first()
            if elegido is None:
                elegido = candidatos.filter(nombre__icontains=texto).first()
            if elegido is not None:
                setattr(organizacion, rol, elegido)
        organizacion.save()


class Migration(migrations.Migration):

    dependencies = [
        ("ciudadanos", "0004_vecino_referencia"),
        ("comunidad", "0003_organizacion_directiva"),
    ]

    operations = [
        migrations.RenameField(
            model_name="organizacion", old_name="presidente", new_name="presidente_texto"
        ),
        migrations.RenameField(
            model_name="organizacion", old_name="tesorero", new_name="tesorero_texto"
        ),
        migrations.RenameField(
            model_name="organizacion", old_name="secretario", new_name="secretario_texto"
        ),
        migrations.AddField(
            model_name="organizacion",
            name="presidente",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="organizaciones_presididas",
                to="ciudadanos.vecino",
                verbose_name="presidente",
            ),
        ),
        migrations.AddField(
            model_name="organizacion",
            name="tesorero",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="organizaciones_tesoreria",
                to="ciudadanos.vecino",
                verbose_name="tesorero",
            ),
        ),
        migrations.AddField(
            model_name="organizacion",
            name="secretario",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="organizaciones_secretaria",
                to="ciudadanos.vecino",
                verbose_name="secretario",
            ),
        ),
        migrations.RunPython(copiar_directiva, migrations.RunPython.noop),
        migrations.RemoveField(model_name="organizacion", name="presidente_texto"),
        migrations.RemoveField(model_name="organizacion", name="tesorero_texto"),
        migrations.RemoveField(model_name="organizacion", name="secretario_texto"),
    ]
