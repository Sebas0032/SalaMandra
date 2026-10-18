from datetime import datetime, time, timedelta
from unittest.mock import patch

import pytest
from django.contrib.auth.hashers import make_password
from django.db import IntegrityError, transaction
from django.urls import reverse
from django.utils import timezone

from reservas import services
from reservas.models import Horario, Reserva, Rol, Sala, SalaHorario, Sancion, TipoSancion, Usuario, UsuarioRol

pytestmark = pytest.mark.django_db


@pytest.fixture
def escenario(client):
    ahora = timezone.make_aware(datetime(2026, 10, 19, 6))  # Lunes
    usuario = Usuario.objects.create(pk=95429, email="95429@salamandra.test", nombre="Luciana", apellido="Soledad", password_hash=make_password("clave"))
    rol = Rol.objects.create(nombre_rol="Solicitante")
    UsuarioRol.objects.create(usuario=usuario, rol=rol)
    sala = Sala.objects.create(nombre_sala="Sala A")
    horarios = [Horario.objects.create(hora_inicio=inicio, hora_fin=fin) for inicio, fin in [
        (time(7, 45), time(9, 45)), (time(10), time(12)), (time(12, 15), time(14, 15)),
    ]]
    bloques = [SalaHorario.objects.create(sala=sala, horario=h) for h in horarios]
    client.post(reverse("login"), {"identificador": str(usuario.pk), "password": "clave"})
    with patch("reservas.services.timezone.localtime", return_value=ahora):
        yield usuario, bloques, ahora


def test_panel_y_reserva_usan_la_identidad_de_la_sesion(client, escenario):
    usuario, bloques, ahora = escenario
    response = client.get(reverse("student_panel"))
    assert response.status_code == 200
    assert b"Sala A" in response.content
    response = client.post(reverse("student_panel"), {
        "id_sala_horario": bloques[0].pk, "actividad": "Tarea", "codigo_usuario": "99999",
    })
    assert response.url == reverse("student_panel")
    reserva = Reserva.objects.get()
    assert reserva.usuario_id == usuario.pk
    assert reserva.fecha == ahora.date()
    assert reserva.estado_reserva == "CONFIRMADA"
    assert b"Luciana Soledad" in client.get(reverse("student_panel")).content


def test_mantenimiento_cancela_y_rechaza_nueva_reserva(escenario):
    usuario, bloques, _ = escenario
    reserva = services.create_student_reservation(usuario.pk, bloques[0].pk, "Tarea")
    admin = Usuario.objects.create(pk=900001, email="admin@test.edu", nombre="Admin", apellido="Test")
    UsuarioRol.objects.create(usuario=admin, rol=Rol.objects.create(nombre_rol="Administrador"))
    services.block_room_schedule_for_maintenance(admin.pk, bloques[0].pk, "Reparación")
    reserva.refresh_from_db()
    assert reserva.estado_reserva == "POR_MANTENIMIENTO"
    with pytest.raises(services.ReservationError, match="mantenimiento"):
        services.create_student_reservation(usuario.pk, bloques[0].pk, "Tarea")
    assert Reserva.objects.count() == 1
    assert Sancion.objects.count() == 0


def test_bloques_consecutivos_y_separados(escenario):
    usuario, bloques, _ = escenario
    services.create_student_reservation(usuario.pk, bloques[0].pk, "Tarea")
    with pytest.raises(services.ReservationError, match="consecutivo"):
        services.create_student_reservation(usuario.pk, bloques[1].pk, "Tarea")
    services.create_student_reservation(usuario.pk, bloques[2].pk, "Proyecto")
    assert Reserva.objects.count() == 2


def test_restriccion_bd_por_fecha_y_estado(escenario):
    usuario, bloques, ahora = escenario
    services.create_student_reservation(usuario.pk, bloques[0].pk, "Tarea")
    with pytest.raises(IntegrityError), transaction.atomic():
        Reserva.objects.create(usuario=usuario, sala_horario=bloques[0], fecha=ahora.date(), tipo_actividad="Examen", estado_reserva="EN_USO")
    Reserva.objects.create(usuario=usuario, sala_horario=bloques[0], fecha=ahora.date(), tipo_actividad="Examen", estado_reserva="POR_MANTENIMIENTO")
    Reserva.objects.create(usuario=usuario, sala_horario=bloques[0], fecha=ahora.date() + timedelta(days=1), tipo_actividad="Examen")
    assert Reserva.objects.count() == 3


def test_sancion_permite_consultar_pero_no_reservar(client, escenario):
    usuario, bloques, ahora = escenario
    tipo = TipoSancion.objects.create(nombre_sancion="Falta", duracion=24)
    Sancion.objects.create(usuario=usuario, tipo_sancion=tipo, motivo="Cancelación", fecha_inicio=ahora-timedelta(hours=1), fecha_fin=ahora+timedelta(hours=23))
    assert client.get(reverse("student_panel")).status_code == 200
    with pytest.raises(services.ReservationError, match="Sanción activa"):
        services.create_student_reservation(usuario.pk, bloques[0].pk, "Tarea")
    assert not Reserva.objects.exists()


def test_fin_de_semana_y_feriados(escenario, settings):
    usuario, bloques, ahora = escenario
    settings.RESERVAS_FERIADOS = [ahora.date().isoformat()]
    with pytest.raises(services.ReservationError, match="feriado"):
        services.create_student_reservation(usuario.pk, bloques[0].pk, "Tarea")
    settings.RESERVAS_FERIADOS = []
    with patch("reservas.services.timezone.localtime", return_value=ahora + timedelta(days=5)):
        with pytest.raises(services.ReservationError, match="fin de semana"):
            services.create_student_reservation(usuario.pk, bloques[0].pk, "Tarea")


def test_bloque_finalizado_se_oculta_y_se_rechaza(escenario):
    usuario, bloques, ahora = escenario
    with patch("reservas.services.timezone.localtime", return_value=ahora.replace(hour=10)):
        assert bloques[0].pk not in [b["id"] for c in services.get_student_panel()["columnas"] for b in c["bloques"]]
        with pytest.raises(services.ReservationError, match="terminó"):
            services.create_student_reservation(usuario.pk, bloques[0].pk, "Tarea")


def test_intervalo_de_limpieza(escenario):
    usuario, bloques, ahora = escenario
    otro = Usuario.objects.create(pk=94186, email="otro@test.edu", nombre="Otro", apellido="Test")
    horario = Horario.objects.create(hora_inicio=time(6), hora_fin=time(7, 35))
    sh = SalaHorario.objects.create(sala=bloques[0].sala, horario=horario)
    Reserva.objects.create(usuario=otro, sala_horario=sh, fecha=ahora.date(), tipo_actividad="Tarea")
    with pytest.raises(services.ReservationError, match="15 minutos"):
        services.create_student_reservation(usuario.pk, bloques[0].pk, "Tarea")
    horario.hora_fin = time(7, 30)
    horario.save()
    services.create_student_reservation(usuario.pk, bloques[0].pk, "Tarea")


def test_anonimo_no_puede_reservar(client):
    assert client.post(reverse("student_panel"), {}).url == reverse("login")


@pytest.mark.parametrize("dias,feriado", [(5, False), (6, False), (0, True)])
def test_dia_no_habilitado_oculta_salas_y_formulario(client, escenario, settings, dias, feriado):
    _, bloques, ahora = escenario
    fecha = ahora + timedelta(days=dias)
    settings.RESERVAS_FERIADOS = [fecha.date().isoformat()] if feriado else []
    with patch("reservas.services.timezone.localtime", return_value=fecha):
        response = client.get(reverse("student_panel"))
        assert response.status_code == 200
        assert "Hoy no se muestran salas" in response.content.decode()
        assert b"Sala A" not in response.content
        assert b"<form" not in response.content
        assert b"Confirmar reserva" not in response.content
        client.post(reverse("student_panel"), {
            "id_sala_horario": bloques[0].pk, "actividad": "Tarea",
        })
        assert not Reserva.objects.exists()
