"""Convierte una base SQLite anterior, que guardaba fechas UTC, a hora de La Paz.

Uso único para bases creadas antes de configurar DATABASES['default']['TIME_ZONE'].
Las bases nuevas ya guardan hora local y no deben ejecutar este comando.
"""

from contextlib import closing
from datetime import datetime, timezone
from pathlib import Path
import sqlite3
from zoneinfo import ZoneInfo

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import connection, transaction


MARCA_CONVERSION = 20261029
ZONA_LOCAL = ZoneInfo("America/La_Paz")
COLUMNAS_FECHA = (
    ("usuarios", "codigo_usuario", ("fecha_creacion",)),
    ("sanciones", "id_sancion", ("fecha_inicio", "fecha_fin", "fecha_retiro")),
    ("reinicios_sanciones", "id", ("fecha",)),
    ("notificaciones", "id_notificacion", ("fecha",)),
    ("auditoria", "id_auditoria", ("fecha_accion",)),
    ("bloqueos", "id_bloqueo", ("fecha",)),
    ("desbloqueos", "id_desbloqueos", ("fecha_desbloqueo",)),
    ("django_migrations", "id", ("applied",)),
)


def _a_hora_local(valor):
    fecha_utc = valor if isinstance(valor, datetime) else datetime.fromisoformat(valor)
    if fecha_utc.tzinfo is None:
        fecha_utc = fecha_utc.replace(tzinfo=timezone.utc)
    return fecha_utc.astimezone(ZONA_LOCAL).replace(tzinfo=None).isoformat(sep=" ")


class Command(BaseCommand):
    help = "Convierte una sola vez las fechas UTC de una base SQLite antigua a America/La_Paz."

    def add_arguments(self, parser):
        parser.add_argument(
            "--apply", action="store_true",
            help="Crea un respaldo y convierte las fechas. Sin esta opción, solo muestra el plan.",
        )

    def handle(self, *args, **options):
        if not settings.USE_TZ or connection.vendor != "sqlite":
            raise CommandError("Este comando requiere SQLite con USE_TZ=True.")
        if connection.settings_dict.get("TIME_ZONE") != "America/La_Paz":
            raise CommandError("Configura DATABASES['default']['TIME_ZONE'] en America/La_Paz.")

        ruta_db = Path(connection.settings_dict["NAME"])
        if not ruta_db.is_file():
            raise CommandError("No existe la base SQLite que se debe convertir.")

        with connection.cursor() as cursor:
            cursor.execute("PRAGMA user_version")
            marca = cursor.fetchone()[0]
            if marca == MARCA_CONVERSION:
                self.stdout.write("Esta base ya fue convertida a hora de La Paz.")
                return
            if marca != 0:
                raise CommandError("La base usa PRAGMA user_version; no se modificará esa marca.")
            cantidades = {}
            for tabla, _, columnas in COLUMNAS_FECHA:
                for columna in columnas:
                    cursor.execute(
                        f'SELECT COUNT(*) FROM "{tabla}" WHERE "{columna}" IS NOT NULL'
                    )
                    cantidades[f"{tabla}.{columna}"] = cursor.fetchone()[0]

        total = sum(cantidades.values())
        if not options["apply"]:
            self.stdout.write(
                f"Se convertirían {total} valores de fecha. "
                "Ejecuta python manage.py convert_legacy_utc --apply solo en una base antigua."
            )
            return

        carpeta_respaldo = Path(settings.BASE_DIR) / ".backups"
        carpeta_respaldo.mkdir(exist_ok=True)
        sello = datetime.now().strftime("%Y%m%d-%H%M%S-%f")
        respaldo = carpeta_respaldo / f"{ruta_db.name}.utc-{sello}.bak"
        try:
            with closing(sqlite3.connect(str(ruta_db), timeout=10)) as origen, closing(
                sqlite3.connect(str(respaldo), timeout=10)
            ) as destino:
                origen.backup(destino)
        except sqlite3.Error as exc:
            raise CommandError(f"No se pudo crear el respaldo: {exc}") from exc

        with transaction.atomic():
            with connection.cursor() as cursor:
                cursor.execute("PRAGMA user_version")
                if cursor.fetchone()[0] != 0:
                    raise CommandError("La base cambió durante el respaldo; no se convirtió.")
                for tabla, clave, columnas in COLUMNAS_FECHA:
                    for columna in columnas:
                        cursor.execute(
                            f'SELECT "{clave}", "{columna}" FROM "{tabla}" '
                            f'WHERE "{columna}" IS NOT NULL'
                        )
                        for identificador, valor in cursor.fetchall():
                            cursor.execute(
                                f'UPDATE "{tabla}" SET "{columna}" = %s '
                                f'WHERE "{clave}" = %s',
                                [_a_hora_local(valor), identificador],
                            )
                cursor.execute(f"PRAGMA user_version = {MARCA_CONVERSION}")

        self.stdout.write(self.style.SUCCESS(
            f"Convertidos {total} valores a hora de La Paz. Respaldo: {respaldo}"
        ))
