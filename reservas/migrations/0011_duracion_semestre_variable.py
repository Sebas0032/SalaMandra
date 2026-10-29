from datetime import datetime

from django.db import migrations, models
from django.utils import timezone


ID_SEMESTRE = 77


def _fin_semestre(fecha):
    local = timezone.localtime(fecha)
    if local.month < 7:
        limite = datetime(local.year, 7, 1)
    else:
        limite = datetime(local.year + 1, 1, 1)
    return timezone.make_aware(limite)


def corregir_semestre(apps, schema_editor):
    TipoSancion = apps.get_model("reservas", "TipoSancion")
    Sancion = apps.get_model("reservas", "Sancion")
    db = schema_editor.connection.alias

    TipoSancion.objects.using(db).filter(pk=ID_SEMESTRE).update(duracion=None)
    sanciones = Sancion.objects.using(db).filter(tipo_sancion_id=ID_SEMESTRE)
    for sancion in sanciones.iterator():
        sancion.fecha_fin = _fin_semestre(sancion.fecha_inicio)
        sancion.save(using=db, update_fields=["fecha_fin"])


def restaurar_marcador(apps, schema_editor):
    TipoSancion = apps.get_model("reservas", "TipoSancion")
    TipoSancion.objects.using(schema_editor.connection.alias).filter(
        pk=ID_SEMESTRE
    ).update(duracion=9999)


class Migration(migrations.Migration):

    dependencies = [
        ("reservas", "0010_notificacion"),
    ]

    operations = [
        migrations.RemoveConstraint(
            model_name="tiposancion",
            name="tipo_sancion_catalogo_fijo",
        ),
        migrations.AlterField(
            model_name="tiposancion",
            name="duracion",
            field=models.IntegerField(blank=True, null=True),
        ),
        migrations.RunPython(corregir_semestre, restaurar_marcador),
        migrations.AddConstraint(
            model_name="tiposancion",
            constraint=models.CheckConstraint(
                condition=(
                    models.Q(id_tipo_sancion=74, duracion=24)
                    | models.Q(id_tipo_sancion=75, duracion=48)
                    | models.Q(id_tipo_sancion=76, duracion=168)
                    | models.Q(id_tipo_sancion=77, duracion__isnull=True)
                ),
                name="tipo_sancion_catalogo_fijo",
            ),
        ),
    ]
