from copy import deepcopy

import pytest
from django.db import connections
from django.db.migrations.executor import MigrationExecutor
from django.utils import timezone


pytestmark = pytest.mark.integration


ANTERIOR = ("reservas", "0004_unicidad_salas_y_horarios")
NUEVA = ("reservas", "0005_rol_unico_sanciones_auditoria")


@pytest.fixture
def base_anterior(tmp_path, settings, django_db_blocker):
    """Ejecuta migraciones reales en una base aislada, aun con --nomigrations."""
    settings.MIGRATION_MODULES = {}
    alias = "prueba_migracion"
    config = deepcopy(connections.databases["default"])
    config["NAME"] = str(tmp_path / "migracion.sqlite3")
    connections.databases[alias] = config
    with django_db_blocker.unblock():
        conexion = connections[alias]
        try:
            executor = MigrationExecutor(conexion)
            executor.migrate([ANTERIOR])
            apps = executor.loader.project_state([ANTERIOR]).apps
            yield conexion, apps
        finally:
            conexion.close()
            del connections[alias]
            del connections.databases[alias]


# Test 97: verifica la migración sin inventar auditorías.
def test_migra_roles_y_sanciones_sin_inventar_auditoria(base_anterior):
    conexion, apps = base_anterior
    db = conexion.alias
    Usuario = apps.get_model("reservas", "Usuario")
    Rol = apps.get_model("reservas", "Rol")
    Asignacion = apps.get_model("reservas", "UsuarioRol")
    admin = Usuario.objects.using(db).create(pk=25, email="admin@test.edu")
    ana = Usuario.objects.using(db).create(pk=10, email="ana@test.edu", password_hash="conservar")
    Usuario.objects.using(db).create(pk=30, email="precargada@test.edu")
    for nombre in ("Estudiante", "Solicitante"):
        rol = Rol.objects.using(db).create(nombre_rol=nombre)
        Asignacion.objects.using(db).create(usuario=ana, rol=rol)
    rol_admin = Rol.objects.using(db).create(nombre_rol="Administrador")
    Asignacion.objects.using(db).create(usuario=admin, rol=rol_admin)
    tipo = apps.get_model("reservas", "TipoSancion").objects.using(db).create(
        nombre_sancion="Cancelación tardía (1ra vez)", duracion=24,
    )
    apps.get_model("reservas", "Sancion").objects.using(db).create(
        usuario=ana, tipo_sancion=tipo, motivo="Motivo original",
        fecha_inicio=timezone.now(), fecha_fin=timezone.now(),
    )

    executor = MigrationExecutor(conexion)
    executor.migrate([NUEVA])
    nuevos = executor.loader.project_state([NUEVA]).apps
    Usuario = nuevos.get_model("reservas", "Usuario")
    assert Usuario.objects.using(db).get(pk=10).password_hash == "conservar"
    assert dict(Usuario.objects.using(db).values_list("pk", "rol__nombre_rol")) == {
        25: "Administrador", 10: "Solicitante", 30: "Solicitante",
    }
    assert set(nuevos.get_model("reservas", "Rol").objects.using(db).values_list("nombre_rol", flat=True)) == {
        "Administrador", "Operante", "Solicitante",
    }
    sancion = nuevos.get_model("reservas", "Sancion").objects.using(db).get()
    assert (sancion.origen, sancion.aplicada_por_id, sancion.motivo) == ("AUTOMATICA", None, "Motivo original")
    assert not nuevos.get_model("reservas", "Auditoria").objects.using(db).exists()


@pytest.mark.parametrize("caso", ["roles_ambiguos", "sancion_sin_autor"])
# Tests 98-99: verifican el rechazo seguro de datos ambiguos.
def test_migracion_rechaza_datos_ambiguos_sin_perderlos(base_anterior, caso):
    conexion, apps = base_anterior
    db = conexion.alias
    usuario = apps.get_model("reservas", "Usuario").objects.using(db).create(pk=10, email="ana@test.edu")
    if caso == "roles_ambiguos":
        for nombre in ("Administrador", "Solicitante"):
            rol = apps.get_model("reservas", "Rol").objects.using(db).create(nombre_rol=nombre)
            apps.get_model("reservas", "UsuarioRol").objects.using(db).create(usuario=usuario, rol=rol)
        mensaje = "único rol"
    else:
        tipo = apps.get_model("reservas", "TipoSancion").objects.using(db).create(nombre_sancion="Sanción manual (24 horas)", duracion=24)
        apps.get_model("reservas", "Sancion").objects.using(db).create(
            usuario=usuario, tipo_sancion=tipo, fecha_inicio=timezone.now(), fecha_fin=timezone.now(),
        )
        mensaje = "sin origen/autor"
    with pytest.raises(RuntimeError, match=mensaje):
        MigrationExecutor(conexion).migrate([NUEVA])
    assert apps.get_model("reservas", "Usuario").objects.using(db).count() == 1
    if caso == "roles_ambiguos":
        assert apps.get_model("reservas", "UsuarioRol").objects.using(db).count() == 2
    else:
        assert apps.get_model("reservas", "Sancion").objects.using(db).count() == 1
