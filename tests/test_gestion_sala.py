import pytest
from datetime import date, time
from django.urls import reverse

from reservas.gestion_salas import (
    GestionSalasError,
    create_room,
    create_room_schedule,
)
from reservas.models import (Bloqueo, Horario, Reserva, Rol, Sala, SalaHorario, Usuario, UsuarioRol,)

pytestmark = pytest.mark.django_db


@pytest.fixture
def admin():
    """Administrador válido para las pruebas."""
    usuario = Usuario.objects.create(
        codigo_usuario=900100, email="admin-gestion@test.edu",
        nombre="Admin", apellido="Pruebas", password_hash="sesion-activa",
    )
    rol = Rol.objects.create(nombre_rol="Administrador")
    UsuarioRol.objects.create(usuario=usuario, rol=rol)
    return usuario


@pytest.fixture
def sala():
    """Sala inicial donde se probarán los intervalos."""
    return Sala.objects.create(nombre_sala="Sala de estudio A")


# PRUEBAS UNITARIAS (3)

def test_duracion_minima_de_120_minutos(admin, sala):
    with pytest.raises(GestionSalasError, match="120 minutos"):
        create_room_schedule(admin.pk, sala.pk, "10:00", "11:30")
    assert SalaHorario.objects.count() == 0
    create_room_schedule(admin.pk, sala.pk, "10:00", "12:00")
    assert SalaHorario.objects.count() == 1


def test_no_superpone_horarios_de_una_sala(admin, sala):
    create_room_schedule(admin.pk, sala.pk, "10:00", "12:00")
    with pytest.raises(GestionSalasError, match="superpone"):
        create_room_schedule(admin.pk, sala.pk, "11:00", "13:00")
    with pytest.raises(GestionSalasError, match="superpone"):
        create_room_schedule(admin.pk, sala.pk, "09:00", "11:00")
    assert SalaHorario.objects.filter(sala=sala).count() == 1


def test_separacion_minima_de_15_minutos(admin, sala):
    create_room_schedule(admin.pk, sala.pk, "10:00", "12:00")
    with pytest.raises(GestionSalasError, match="15 minutos"):
        create_room_schedule(admin.pk, sala.pk, "12:10", "14:10")
    create_room_schedule(admin.pk, sala.pk, "12:15", "14:15")
    assert SalaHorario.objects.filter(sala=sala).count() == 2