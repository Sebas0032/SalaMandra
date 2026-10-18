from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("reservas", "0002_alter_usuario_codigo_usuario")]
    operations = [
        migrations.AddConstraint(
            model_name="reserva",
            constraint=models.UniqueConstraint(
                fields=("sala_horario", "fecha"),
                condition=models.Q(estado_reserva__in=["CONFIRMADA", "EN_USO"]),
                name="uq_reserva_activa_horario_fecha",
            ),
        ),
    ]