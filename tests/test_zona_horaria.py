from datetime import datetime, timezone

import pytest
from django.db import connection

from reservas.management.commands.convert_legacy_utc import _a_hora_local
from reservas.models import Rol, Usuario


pytestmark = pytest.mark.integration


# Test 100: verifica la conversión histórica de UTC a La Paz.
def test_conversion_utc_a_la_paz_conserva_microsegundos_y_cambia_dia():
    assert _a_hora_local("2026-01-01 02:15:30.123456") == (
        "2025-12-31 22:15:30.123456"
    )


@pytest.mark.django_db
# Test 82: verifica el almacenamiento de fechas en hora de La Paz.
def test_sqlite_guarda_datetime_en_hora_de_la_paz_y_django_conserva_instante():
    instante = datetime(2026, 10, 29, 20, 50, 32, 514890, tzinfo=timezone.utc)
    usuario = Usuario.objects.create(
        codigo_usuario=123456,
        rol=Rol.objects.create(nombre_rol="Solicitante"),
        email="123456@test.edu",
        nombre="Prueba",
        apellido="Horario",
        fecha_creacion=instante,
    )

    with connection.cursor() as cursor:
        cursor.execute(
            'SELECT "fecha_creacion" FROM "usuarios" WHERE "codigo_usuario" = %s',
            [usuario.pk],
        )
        valor_sqlite = cursor.fetchone()[0]

    assert valor_sqlite == datetime(2026, 10, 29, 16, 50, 32, 514890)
    assert Usuario.objects.get(pk=usuario.pk).fecha_creacion == instante
