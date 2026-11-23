from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("comunidad", "0002_organizacion_situacion_organizacion_subtipo_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="organizacion",
            name="presidente",
            field=models.CharField(
                blank=True, max_length=120, verbose_name="presidente"
            ),
        ),
        migrations.AddField(
            model_name="organizacion",
            name="tesorero",
            field=models.CharField(blank=True, max_length=120, verbose_name="tesorero"),
        ),
        migrations.AddField(
            model_name="organizacion",
            name="secretario",
            field=models.CharField(
                blank=True, max_length=120, verbose_name="secretario"
            ),
        ),
    ]
