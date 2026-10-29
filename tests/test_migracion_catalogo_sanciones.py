from copy import deepcopy
from datetime import datetime, timedelta

import pytest
from django.db import connections
from django.db.migrations.executor import MigrationExecutor
from django.utils import timezone


ANTERIOR = ("reservas", "0008_sancion_fecha_retiro_sancion_retirada_por_and_more")
NUEVA = ("reservas", "0009_tiposancion_tipo_sancion_catalogo_fijo")
ANTERIOR_SEMESTRE = ("reservas", "0010_notificacion")
NUEVA_SEMESTRE = ("reservas", "0011_duracion_semestre_variable")

pytestmark = pytest.mark.django_db


def test_migracion_consolida_tipos_sin_borrar_sanciones(
    tmp_path, settings, django_db_blocker
):
    settings.MIGRATION_MODULES = {}
    alias = "prueba_catalogo_sanciones"
    config = deepcopy(connections.databases["default"])
    config["NAME"] = str(tmp_path / "catalogo.sqlite3")
    connections.databases[alias] = config

    with django_db_blocker.unblock():
        conexion = connections[alias]
        try:
            executor = MigrationExecutor(conexion)
            executor.migrate([ANTERIOR])
            apps = executor.loader.project_state([ANTERIOR]).apps
            Rol = apps.get_model("reservas", "Rol")
            Usuario = apps.get_model("reservas", "Usuario")
            TipoSancion = apps.get_model("reservas", "TipoSancion")
            Sancion = apps.get_model("reservas", "Sancion")
            rol = Rol.objects.using(alias).get(nombre_rol="Solicitante")
            usuario = Usuario.objects.using(alias).create(
                pk=101145, rol=rol, email="estudiante@test.edu",
                nombre="Sebastian", apellido="Cruz",
            )
            for tipo_id, nombre, duracion in (
                (74, "Cancelación tardía (1ra vez)", 24),
                (75, "Cancelación tardía (2da vez)", 48),
                (76, "Cancelación tardía (3ra vez)", 168),
                (77, "Cancelación tardía (4ta vez, todo el semestre)", 9999),
                (78, "Sanción manual (1 semana)", 168),
            ):
                TipoSancion.objects.using(alias).create(
                    pk=tipo_id, nombre_sancion=nombre, duracion=duracion
                )
            ahora = timezone.now()
            for numero in range(2):
                Sancion.objects.using(alias).create(
                    usuario=usuario, tipo_sancion_id=78, origen="AUTOMATICA",
                    motivo=f"Histórica {numero}", fecha_inicio=ahora,
                    fecha_fin=ahora + timedelta(hours=168),
                )

            MigrationExecutor(conexion).migrate([NUEVA])
            nuevas = MigrationExecutor(conexion).loader.project_state([NUEVA]).apps
            tipos = nuevas.get_model("reservas", "TipoSancion").objects.using(alias)
            sanciones = nuevas.get_model("reservas", "Sancion").objects.using(alias)
            assert set(tipos.values_list("pk", flat=True)) == {74, 75, 76, 77}
            assert sanciones.count() == 2
            assert set(sanciones.values_list("tipo_sancion_id", flat=True)) == {76}
        finally:
            conexion.close()
            del connections[alias]
            del connections.databases[alias]


def test_migracion_corrige_duracion_y_fecha_fin_del_semestre(
    tmp_path, settings, django_db_blocker
):
    settings.MIGRATION_MODULES = {}
    alias = "prueba_duracion_semestre"
    config = deepcopy(connections.databases["default"])
    config["NAME"] = str(tmp_path / "semestre.sqlite3")
    connections.databases[alias] = config

    with django_db_blocker.unblock():
        conexion = connections[alias]
        try:
            executor = MigrationExecutor(conexion)
            executor.migrate([ANTERIOR_SEMESTRE])
            apps = executor.loader.project_state([ANTERIOR_SEMESTRE]).apps
            Rol = apps.get_model("reservas", "Rol")
            Usuario = apps.get_model("reservas", "Usuario")
            Sancion = apps.get_model("reservas", "Sancion")
            estudiante = Usuario.objects.using(alias).create(
                pk=101145,
                rol=Rol.objects.using(alias).get(nombre_rol="Solicitante"),
                email="semestre@test.edu",
                nombre="Estudiante",
                apellido="Semestre",
            )
            inicio = timezone.make_aware(datetime(2026, 10, 15, 9))
            sancion = Sancion.objects.using(alias).create(
                usuario=estudiante,
                tipo_sancion_id=77,
                origen="AUTOMATICA",
                motivo="Todo el semestre",
                fecha_inicio=inicio,
                fecha_fin=inicio + timedelta(hours=9999),
            )

            MigrationExecutor(conexion).migrate([NUEVA_SEMESTRE])
            nuevas = MigrationExecutor(conexion).loader.project_state(
                [NUEVA_SEMESTRE]
            ).apps
            tipo = nuevas.get_model("reservas", "TipoSancion").objects.using(
                alias
            ).get(pk=77)
            sancion_actualizada = nuevas.get_model(
                "reservas", "Sancion"
            ).objects.using(alias).get(pk=sancion.pk)

            assert tipo.duracion is None
            assert sancion_actualizada.fecha_fin == timezone.make_aware(
                datetime(2027, 1, 1)
            )
        finally:
            conexion.close()
            del connections[alias]
            del connections.databases[alias]
