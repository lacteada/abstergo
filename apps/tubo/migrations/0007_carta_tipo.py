from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("tubo", "0006_tareatubo_carta"),
    ]

    operations = [
        migrations.AddField(
            model_name="carta",
            name="tipo",
            field=models.CharField(
                choices=[
                    ("correspondencia", "Correspondencia"),
                    ("felicitacion", "Felicitación"),
                    ("regano", "Regaño"),
                ],
                default="correspondencia",
                max_length=16,
                verbose_name="tipo",
            ),
        ),
    ]
