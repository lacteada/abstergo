from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("cuentas", "0007_usuario_cargo"),
    ]

    operations = [
        migrations.AddField(
            model_name="usuario",
            name="guia_vista",
            field=models.BooleanField(default=False, verbose_name="guía vista"),
        ),
    ]
