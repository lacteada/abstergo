from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("tubo", "0005_carta"),
    ]

    operations = [
        migrations.AddField(
            model_name="tareatubo",
            name="carta",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="compromisos",
                to="tubo.carta",
                verbose_name="carta de origen",
            ),
        ),
    ]
