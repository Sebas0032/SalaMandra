from datetime import datetime, time
from unittest.mock import patch

import pytest
from django.contrib.auth.hashers import make_password
from django.urls import reverse
from django.utils import timezone

from reservas import services
from reservas.models import Auditoria, Horario, Notificacion, Reserva, Rol, Sala, SalaHorario, Sancion, Usuario


pytestmark = pytest.mark.django_db


@pytest.fixture
def escenario(client):
    ahora = timezone.make_aware(datetime(2026, 10, 29, 8))
    admin = Usuario.objects.create(
        pk=1001, rol=Rol.objects.create(nombre_rol=Rol.Nombre.ADMINISTRADOR),
        email="admin@upb.edu", nombre="Admin", apellido="Prueba",
        password_hash=make_password("clave-admin"),
    )
    estudiante = Usuario.objects.create(
        pk=1002, rol=Rol.objects.create(nombre_rol=Rol.Nombre.SOLICITANTE),
        email="alumno@upb.edu", nombre="Alumno", apellido="Prueba",
        password_hash=make_password("clave-alumno"),
    )
    operante = Usuario.objects.create(
        pk=1003, rol=Rol.objects.create(nombre_rol=Rol.Nombre.OPERANTE),
        email="operante@upb.edu", nombre="Operante", apellido="Prueba",
        password_hash=make_password("clave-operante"),
    )
    horarios = [
        Horario.objects.create(hora_inicio=inicio, hora_fin=fin)
        for inicio, fin in [
            (time(9), time(10)), (time(10, 15), time(11, 15)),
            (time(11, 30), time(12, 30)), (time(13), time(14)),
        ]
    ]
    sala_a = Sala.objects.create(nombre_sala="Sala A")
    sala_b = Sala.objects.create(nombre_sala="Sala B")
    bloques_a = [SalaHorario.objects.create(sala=sala_a, horario=h) for h in horarios]
    bloques_b = [SalaHorario.objects.create(sala=sala_b, horario=h) for h in horarios]
    return client, admin, estudiante, operante, bloques_a, bloques_b, ahora


def test_admin_reserva_para_si_mismo_bloques_consecutivos_y_mismo_bloque(escenario):
    _, admin, estudiante, _, a, b, ahora = escenario
    with patch("reservas.services.timezone.localtime", return_value=ahora):
        servicios = [
            services.create_student_reservation(admin.pk, a[0].pk, "Tarea"),
            services.create_student_reservation(admin.pk, a[1].pk, "Proyecto"),
            services.create_student_reservation(admin.pk, b[1].pk, "Examen"),
        ]
        services.create_student_reservation(estudiante.pk, b[2].pk, "Tarea")
        with pytest.raises(services.ReservationError, match="consecutivo"):
            services.create_student_reservation(estudiante.pk, b[3].pk, "Proyecto")
    assert all(r.usuario == admin for r in servicios)
    assert Reserva.objects.filter(usuario=admin).count() == 3
    assert Auditoria.objects.filter(actor=admin, accion="CREAR").count() == 3


def test_admin_modifica_reserva_iniciada_a_otro_bloque_y_operante_no(escenario):
    client, admin, estudiante, operante, a, b, ahora = escenario
    reserva = Reserva.objects.create(
        usuario=estudiante, sala_horario=a[0], fecha=ahora.date(), tipo_actividad="Tarea"
    )
    tarde = ahora.replace(hour=9, minute=30)
    with patch("reservas.services.timezone.localtime", return_value=tarde):
        with pytest.raises(services.ReservationError, match="60 minutos"):
            services.modify_reservation(operante.pk, reserva.pk, b[1].pk)
        client.post(reverse("login"), {"identificador": str(admin.pk), "password": "clave-admin"})
        respuesta = client.get(reverse("modify_reservation", args=[reserva.pk]))
        assert respuesta.status_code == 200
        services.modify_reservation(admin.pk, reserva.pk, b[1].pk)
    reserva.refresh_from_db()
    assert reserva.sala_horario == b[1]
    assert Auditoria.objects.get(reserva=reserva, accion="MODIFICAR").actor == admin


def test_admin_cancela_reserva_iniciada_sin_sancion_y_notifica(escenario):
    _, admin, estudiante, operante, a, _, ahora = escenario
    reserva = Reserva.objects.create(
        usuario=estudiante, sala_horario=a[0], fecha=ahora.date(), tipo_actividad="Tarea"
    )
    tarde = ahora.replace(hour=9, minute=30)
    with patch("reservas.services.timezone.localtime", return_value=tarde):
        with pytest.raises(services.ReservationError, match="ya comenzó"):
            services.cancel_reservation(operante.pk, reserva.pk)
        resultado = services.cancel_reservation(admin.pk, reserva.pk)
    reserva.refresh_from_db()
    assert reserva.estado_reserva == Reserva.ESTADO_CANCELADA
    assert resultado["sancion"] is None
    assert not Sancion.objects.exists()
    assert Notificacion.objects.get(reserva=reserva).usuario == estudiante


def test_admin_mantenimiento_tras_inicio_y_operante_restringido(escenario):
    _, admin, estudiante, operante, a, b, ahora = escenario
    reserva = Reserva.objects.create(
        usuario=estudiante, sala_horario=a[0], fecha=ahora.date(), tipo_actividad="Tarea"
    )
    tarde = ahora.replace(hour=9, minute=30)
    with patch("reservas.services.timezone.localtime", return_value=tarde):
        with pytest.raises(services.MaintenanceAlreadyStartedError):
            services.block_room_schedule_for_maintenance(operante.pk, b[0].pk, "Reparación")
        services.block_room_schedule_for_maintenance(admin.pk, a[0].pk, "Reparación")
    reserva.refresh_from_db()
    assert reserva.estado_reserva == Reserva.ESTADO_POR_MANTENIMIENTO
    assert Notificacion.objects.get(reserva=reserva).usuario == estudiante


def test_panel_admin_muestra_acciones_de_reserva_iniciada(escenario):
    client, admin, _, _, a, _, ahora = escenario
    reserva = Reserva.objects.create(
        usuario=admin, sala_horario=a[0], fecha=ahora.date(), tipo_actividad="Tarea"
    )
    client.post(reverse("login"), {"identificador": str(admin.pk), "password": "clave-admin"})
    tarde = ahora.replace(hour=9, minute=30)
    with patch("reservas.services.timezone.localtime", return_value=tarde):
        panel = client.get(reverse("student_panel"))
        cancelaciones = client.get(reverse("admin_cancellations"))
    assert reverse("modify_reservation", args=[reserva.pk]) in panel.content.decode()
    assert reverse("cancel_reservation", args=[reserva.pk]) in panel.content.decode()
    assert reverse("admin_cancel_reservation", args=[reserva.pk]) in cancelaciones.content.decode()
