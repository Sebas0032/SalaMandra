
"""
Pruebas esenciales de backend para RES-CU-02:
Bloqueo por Mantenimiento.

Ejecución:
python -m pytest tests/sesion12/test_mantenimiento_sesion12.py -v
"""

from datetime import datetime, time, timedelta
from unittest.mock import patch

import pytest
from django.contrib.auth.hashers import make_password
from django.utils import timezone

from reservas import services
from reservas.models import (Bloqueo, Horario, Reserva, Rol, Sala, SalaHorario, Sancion, Usuario,)


pytestmark = pytest.mark.django_db

PASSWORD = "clave-de-prueba-123"
MOTIVO = "Fuga de agua"

@pytest.fixture(autouse=True)
def hasher_rapido(settings):
    """Utiliza un hash rápido durante las pruebas."""
    settings.PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]


@pytest.fixture(autouse=True)
def antes_del_inicio_del_horario():
    ahora = timezone.make_aware(
        datetime.combine(timezone.localdate(), time(9, 0))
    )
    with patch("reservas.services.timezone.localtime", return_value=ahora):
        yield


@pytest.fixture
def manana():
    """Devuelve la fecha del día siguiente."""
    return timezone.localdate() + timedelta(days=1)


def crear_usuario(codigo_usuario, email, nombre, rol):
    """Crea un usuario de prueba y le asigna un rol."""
    usuario = Usuario.objects.create(rol=rol, codigo_usuario=codigo_usuario, email=email, nombre=nombre, apellido="Test", estado_usuario=True, password_hash=make_password(PASSWORD),)
    return usuario


@pytest.fixture
def admin():
    """Crea un administrador para las pruebas."""
    rol = Rol.objects.get_or_create(nombre_rol=services.ROL_ADMINISTRADOR)[0]
    return crear_usuario(900001, "admin@test.edu", "Admin", rol)


@pytest.fixture
def estudiante():
    """Crea un estudiante para las pruebas."""
    rol = Rol.objects.get_or_create(nombre_rol="Solicitante")[0]

    return crear_usuario(900002, "estudiante@test.edu", "Luciana", rol,)


@pytest.fixture
def sh_a_manana():
    """Crea una sala con un horario disponible."""
    sala = Sala.objects.create(nombre_sala="Sala A")

    horario = Horario.objects.create(hora_inicio=time(10, 0), hora_fin=time(12, 0),)

    return SalaHorario.objects.create(sala=sala, horario=horario,)


@pytest.fixture
def reserva(estudiante, sh_a_manana, manana):
    """Crea una reserva asociada al horario de prueba."""
    return Reserva.objects.create(
        usuario=estudiante,
        sala_horario=sh_a_manana,
        tipo_actividad="Estudios",
        fecha=manana,
    )


# ============================================================
# Los tres casos solicitados para la Sesión 12
# ============================================================

class TestMantenimientoSesion12:

    def test_bloqueo_exitoso_y_cancelacion_sin_sancion(self, admin, estudiante, sh_a_manana, reserva,):
        """
        Caso válido:
        El administrador bloquea el horario, la reserva pasa
        a POR_MANTENIMIENTO y el estudiante no recibe sanción.
        """
        services.block_room_schedule_for_maintenance(admin.codigo_usuario, sh_a_manana.id_sala_horario, MOTIVO,)

        sh_a_manana.refresh_from_db()
        reserva.refresh_from_db()

        assert (sh_a_manana.estado_sala_horario == SalaHorario.ESTADO_MANTENIMIENTO)

        assert (reserva.estado_reserva == Reserva.ESTADO_POR_MANTENIMIENTO)

        assert not Sancion.objects.filter(usuario=estudiante).exists()

    def test_impide_doble_bloqueo(self,admin,sh_a_manana,):
        """
        Caso límite:
        El segundo bloqueo debe rechazarse y no debe crear
        un segundo registro de bloqueo.
        """
        services.block_room_schedule_for_maintenance(admin.codigo_usuario,sh_a_manana.id_sala_horario, MOTIVO,)

        cantidad_antes = Bloqueo.objects.filter(sala_horario=sh_a_manana).count()

        with pytest.raises(services.ScheduleAlreadyBlockedError):services.block_room_schedule_for_maintenance(admin.codigo_usuario,sh_a_manana.id_sala_horario,"Otro motivo",)

        cantidad_despues = Bloqueo.objects.filter(sala_horario=sh_a_manana).count()

        assert cantidad_antes == 1
        assert cantidad_despues == cantidad_antes

    def test_estudiante_no_puede_bloquear(self, estudiante, sh_a_manana, reserva,):
        """
        Caso de rechazo:
        Un estudiante no autorizado no puede bloquear el horario.
        El sistema debe lanzar NotAuthorizedError y mantener
        disponible el horario.
        """
        with pytest.raises(services.NotAuthorizedError):
            services.block_room_schedule_for_maintenance(estudiante.codigo_usuario, sh_a_manana.id_sala_horario, MOTIVO,)

        sh_a_manana.refresh_from_db()
        reserva.refresh_from_db()

        assert (sh_a_manana.estado_sala_horario== SalaHorario.ESTADO_DISPONIBLE)
        assert (reserva.estado_reserva== Reserva.ESTADO_CONFIRMADA)
        assert not Bloqueo.objects.filter(sala_horario=sh_a_manana).exists()
        assert not Sancion.objects.filter(usuario=estudiante).exists()
