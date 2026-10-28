from django.contrib.auth.hashers import make_password
from django.db import migrations


CODIGO_OPERANTE = 900003
EMAIL_OPERANTE = "operante@salamandra.upb.edu"


def crear_usuario_operante(apps, schema_editor):
    db = schema_editor.connection.alias
    Rol = apps.get_model("reservas", "Rol")
    Usuario = apps.get_model("reservas", "Usuario")
    rol = Rol.objects.using(db).get(nombre_rol="Operante")

    por_codigo = Usuario.objects.using(db).filter(pk=CODIGO_OPERANTE).first()
    por_email = Usuario.objects.using(db).filter(email=EMAIL_OPERANTE).first()
    if por_codigo and por_codigo.email != EMAIL_OPERANTE:
        raise RuntimeError(
            f"El código {CODIGO_OPERANTE} ya pertenece a otro usuario."
        )
    if por_email and por_email.pk != CODIGO_OPERANTE:
        raise RuntimeError(
            f"El correo {EMAIL_OPERANTE} ya pertenece a otro usuario."
        )
    if por_codigo is None:
        Usuario.objects.using(db).create(
            codigo_usuario=CODIGO_OPERANTE,
            rol=rol,
            email=EMAIL_OPERANTE,
            nombre="Operante",
            apellido="SalaMandra",
            estado_usuario=True,
            password_hash=make_password("Operante_2026!"),
        )


class Migration(migrations.Migration):
    dependencies = [
        ("reservas", "0005_rol_unico_sanciones_auditoria"),
    ]

    operations = [
        migrations.RunPython(crear_usuario_operante, migrations.RunPython.noop),
    ]
