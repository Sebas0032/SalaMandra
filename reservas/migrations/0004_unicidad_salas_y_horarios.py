"""Impide duplicar nombres de sala y bloques horarios a nivel de BD."""

from django.db import migrations, models
from django.db.models.functions import Lower, Trim


class Migration(migrations.Migration):
    dependencies = [
        ("reservas", "0003_reserva_activa_unica"),
    ]

    operations = [
        migrations.AddConstraint(
            model_name="sala",
            constraint=models.UniqueConstraint(
                Lower(Trim("nombre_sala")), name="uq_sala_nombre_normalizado"
            ),
        ),
        migrations.AddConstraint(
            model_name="horario",
            constraint=models.UniqueConstraint(
                fields=["hora_inicio", "hora_fin"], name="uq_horario_intervalo"
            ),
        ),
    ]
