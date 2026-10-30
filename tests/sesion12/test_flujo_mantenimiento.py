"""Contrato esencial de la Sesion 12 para el bloqueo por mantenimiento."""

from datetime import datetime, time
from unittest.mock import patch

import pytest
from django.utils import timezone

from reservas import services
from reservas.models import (
    Bloqueo,
    Horario,
    Reserva,
    Rol,
    Sala,
    SalaHorario,
    Sancion,
    Usuario,
)


pytestmark = [pytest.mark.django_db, pytest.mark.integration]
MOTIVO = "Fuga de agua"


@pytest.fixture
def escenario_mantenimiento():
    administrador = Usuario.objects.create(
        codigo_usuario=910001,
        rol=Rol.objects.get_or_create(nombre_rol=Rol.Nombre.ADMINISTRADOR)[0],
        email="admin-sesion12@test.edu",
        nombre="Admin",
        apellido="Sesion12",
        password_hash="registrada",
    )
    solicitante = Usuario.objects.create(
        codigo_usuario=910002,
        rol=Rol.objects.get_or_create(nombre_rol=Rol.Nombre.SOLICITANTE)[0],
        email="solicitante-sesion12@test.edu",
        nombre="Solicitante",
        apellido="Sesion12",
        password_hash="registrada",
    )
    horario = Horario.objects.create(
        hora_inicio=time(10, 0),
        hora_fin=time(12, 0),
    )
    sala_horario = SalaHorario.objects.create(
        sala=Sala.objects.create(nombre_sala="Sala Sesion 12"),
        horario=horario,
    )
    ahora = timezone.make_aware(datetime(2026, 10, 29, 9, 0))
    reserva = Reserva.objects.create(
        usuario=solicitante,
        sala_horario=sala_horario,
        tipo_actividad="Tarea",
        fecha=ahora.date(),
    )

    with patch("reservas.services.timezone.localtime", return_value=ahora):
        yield administrador, solicitante, sala_horario, reserva


# Test 101: verifica el bloqueo exitoso y la ausencia de sancion.
def test_bloqueo_exitoso_cambia_reserva_sin_sancionar(
    escenario_mantenimiento,
):
    administrador, solicitante, sala_horario, reserva = escenario_mantenimiento

    services.block_room_schedule_for_maintenance(
        administrador.pk,
        sala_horario.pk,
        MOTIVO,
    )

    sala_horario.refresh_from_db()
    reserva.refresh_from_db()
    bloqueo = Bloqueo.objects.get()
    assert sala_horario.estado_sala_horario == SalaHorario.ESTADO_MANTENIMIENTO
    assert reserva.estado_reserva == Reserva.ESTADO_POR_MANTENIMIENTO
    assert bloqueo.usuario == administrador
    assert bloqueo.motivo == MOTIVO
    assert not Sancion.objects.filter(usuario=solicitante).exists()


# Test 102: verifica que un segundo bloqueo sea rechazado.
def test_doble_bloqueo_no_crea_otro_registro(escenario_mantenimiento):
    administrador, _, sala_horario, _ = escenario_mantenimiento
    services.block_room_schedule_for_maintenance(
        administrador.pk,
        sala_horario.pk,
        MOTIVO,
    )

    with pytest.raises(services.ScheduleAlreadyBlockedError):
        services.block_room_schedule_for_maintenance(
            administrador.pk,
            sala_horario.pk,
            "Segundo intento",
        )

    assert Bloqueo.objects.filter(sala_horario=sala_horario).count() == 1


# Test 103: verifica que un Solicitante no pueda bloquear un horario.
def test_solicitante_sin_permiso_no_modifica_el_horario(
    escenario_mantenimiento,
):
    _, solicitante, sala_horario, reserva = escenario_mantenimiento

    with pytest.raises(services.NotAuthorizedError):
        services.block_room_schedule_for_maintenance(
            solicitante.pk,
            sala_horario.pk,
            MOTIVO,
        )

    sala_horario.refresh_from_db()
    reserva.refresh_from_db()
    assert sala_horario.estado_sala_horario == SalaHorario.ESTADO_DISPONIBLE
    assert reserva.estado_reserva == Reserva.ESTADO_CONFIRMADA
    assert not Bloqueo.objects.exists()
    assert not Sancion.objects.filter(usuario=solicitante).exists()
