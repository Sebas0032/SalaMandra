import pytest
from datetime import date, time, timedelta
from django.contrib.auth.hashers import make_password
from django.urls import reverse
from django.utils import timezone

from reservas.gestion_salas import (
    GestionSalasError,
    create_room,
    create_room_schedule,
    remove_room_schedule,
)
from reservas import services
from reservas.models import (Bloqueo, Horario, Reserva, Rol, Sala, SalaHorario, Usuario,)

pytestmark = pytest.mark.django_db


@pytest.fixture(autouse=True)
def habilitar_gestion_solo_para_probar_la_logica_existente(settings):
    settings.GESTION_SALAS_HABILITADA = True


@pytest.fixture
def admin():
    """Administrador válido para las pruebas."""
    usuario = Usuario.objects.create(
        rol=Rol.objects.get_or_create(nombre_rol="Administrador")[0],
        codigo_usuario=900100, email="admin-gestion@test.edu",
        nombre="Admin", apellido="Pruebas", password_hash=make_password("clave-admin"),
    )
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


def test_retirar_horario_conserva_historial_y_permiso_para_reasignarlo(admin, sala):
    asignacion = create_room_schedule(admin.pk, sala.pk, "10:00", "12:00")
    estudiante = Usuario.objects.create(
        pk=900101, rol=Rol.objects.get_or_create(nombre_rol="Solicitante")[0],
        email="estudiante-gestion@test.edu", nombre="Estudiante",
        apellido="Prueba", password_hash=make_password("clave-estudiante"),
    )
    reserva_pasada = Reserva.objects.create(
        usuario=estudiante, sala_horario=asignacion,
        fecha=timezone.localdate() - timedelta(days=1),
        tipo_actividad="Tarea", estado_reserva=Reserva.ESTADO_CANCELADA,
    )

    remove_room_schedule(admin.pk, asignacion.pk)
    asignacion.refresh_from_db()
    assert asignacion.estado_sala_horario == SalaHorario.ESTADO_RETIRADO
    assert Reserva.objects.get(pk=reserva_pasada.pk).sala_horario == asignacion
    assert not services.get_sala_horarios().filter(pk=asignacion.pk).exists()
    assert all(
        bloque["id"] != asignacion.pk
        for columna in services.get_student_panel(estudiante.pk)["columnas"]
        for bloque in columna["bloques"]
    )

    restaurada = create_room_schedule(admin.pk, sala.pk, "10:00", "12:00")
    assert restaurada.pk == asignacion.pk
    assert restaurada.estado_sala_horario == SalaHorario.ESTADO_DISPONIBLE
    assert SalaHorario.objects.filter(sala=sala).count() == 1


def test_no_retirar_horario_con_reserva_activa(admin, sala):
    asignacion = create_room_schedule(admin.pk, sala.pk, "10:00", "12:00")
    estudiante = Usuario.objects.create(
        pk=900101, rol=Rol.objects.get_or_create(nombre_rol="Solicitante")[0],
        email="estudiante-gestion@test.edu", nombre="Estudiante", apellido="Prueba",
    )
    reserva = Reserva.objects.create(
        usuario=estudiante, sala_horario=asignacion,
        fecha=timezone.localdate() + timedelta(days=1), tipo_actividad="Tarea",
    )
    with pytest.raises(GestionSalasError, match="reservas activas"):
        remove_room_schedule(admin.pk, asignacion.pk)
    asignacion.refresh_from_db()
    assert asignacion.estado_sala_horario == SalaHorario.ESTADO_DISPONIBLE
    assert Reserva.objects.filter(pk=reserva.pk).exists()


def test_solo_administrador_puede_retirar_un_horario(client, admin, sala):
    asignacion = create_room_schedule(admin.pk, sala.pk, "10:00", "12:00")
    usuario = Usuario.objects.create(
        pk=900101, rol=Rol.objects.get_or_create(nombre_rol="Solicitante")[0],
        email="estudiante-gestion@test.edu", nombre="Estudiante",
        apellido="Prueba", password_hash=make_password("clave-estudiante"),
    )
    with pytest.raises(GestionSalasError, match="Solo un administrador"):
        remove_room_schedule(usuario.pk, asignacion.pk)
    client.post(reverse("login"), {
        "identificador": str(usuario.pk), "password": "clave-estudiante",
    })
    respuesta = client.post(reverse("gestion_salas"), {
        "accion": "retirar_horario", "id_sala_horario": asignacion.pk,
    })
    assert respuesta.status_code == 403

    client.get(reverse("logout"))
    client.post(reverse("login"), {
        "identificador": str(admin.pk), "password": "clave-admin",
    })
    pagina = client.get(reverse("gestion_salas"))
    assert b"Retirar" in pagina.content
    respuesta = client.post(reverse("gestion_salas"), {
        "accion": "retirar_horario", "id_sala_horario": asignacion.pk,
    })
    assert respuesta.status_code == 302
    asignacion.refresh_from_db()
    assert asignacion.estado_sala_horario == SalaHorario.ESTADO_RETIRADO
    pagina = client.get(reverse("gestion_salas"))
    assert b"Retirar" not in pagina.content
