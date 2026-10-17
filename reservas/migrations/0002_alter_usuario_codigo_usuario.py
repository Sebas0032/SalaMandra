from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("reservas", "0001_initial"),
    ]

    operations = [
        migrations.AlterField(
            model_name="usuario",
            name="codigo_usuario",
            field=models.BigIntegerField(primary_key=True, serialize=False),
        ),
    ]
