from datetime import datetime, time, timedelta
from unittest.mock import patch

import pytest
from django.contrib.auth.hashers import make_password
from django.db import IntegrityError, transaction
from django.urls import reverse
from django.utils import timezone

from reservas import services
from reservas.models import Auditoria, Horario, Reserva, Rol, Sala, SalaHorario, Sancion, TipoSancion, Usuario

pytestmark = pytest.mark.django_db


@pytest.fixture
def escenario(client):
    ahora = timezone.make_aware(datetime(2026, 10, 19, 6))  # Lunes
    usuario = Usuario.objects.create(rol=Rol.objects.get_or_create(nombre_rol="Solicitante")[0], pk=95429, email="95429@salamandra.test", nombre="Luciana", apellido="Soledad", password_hash=make_password("clave"))
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
        "codigo_actor": "99999",
    })
    assert response.url == reverse("student_panel")
    reserva = Reserva.objects.get()
    assert reserva.usuario_id == usuario.pk
    assert Auditoria.objects.get(reserva=reserva).actor_id == usuario.pk
    assert reserva.fecha == ahora.date()
    assert reserva.estado_reserva == "CONFIRMADA"
    assert b"Luciana Soledad" in client.get(reverse("student_panel")).content


def test_mantenimiento_cancela_y_rechaza_nueva_reserva(escenario):
    usuario, bloques, _ = escenario
    reserva = services.create_student_reservation(usuario.pk, bloques[0].pk, "Tarea")
    admin = Usuario.objects.create(rol=Rol.objects.get_or_create(nombre_rol="Administrador")[0], pk=900001, email="admin@test.edu", nombre="Admin", apellido="Test")
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
    Sancion.objects.create(origen=Sancion.Origen.AUTOMATICA, usuario=usuario, tipo_sancion=tipo, motivo="Cancelación", fecha_inicio=ahora-timedelta(hours=1), fecha_fin=ahora+timedelta(hours=23))
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
    otro = Usuario.objects.create(rol=Rol.objects.get_or_create(nombre_rol="Solicitante")[0], pk=94186, email="otro@test.edu", nombre="Otro", apellido="Test")
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


def test_modificar_reserva_cambia_sala_y_conserva_la_misma_fila(client, escenario):
    usuario, bloques, _ = escenario
    reserva = services.create_student_reservation(
        usuario.pk, bloques[1].pk, "Proyecto"
    )
    sala_b = Sala.objects.create(nombre_sala="Sala B")
    destino = SalaHorario.objects.create(
        sala=sala_b, horario=bloques[1].horario
    )

    response = client.get(
        reverse("modify_reservation", args=[reserva.pk])
    )
    assert response.status_code == 200
    assert b"Sala B" in response.content

    response = client.post(
        reverse("modify_reservation", args=[reserva.pk]),
        {"id_sala_horario": destino.pk},
    )
    assert response.url == reverse("student_panel")
    reserva.refresh_from_db()
    assert Reserva.objects.count() == 1
    assert reserva.sala_horario == destino
    assert reserva.tipo_actividad == "Proyecto"


def test_modificacion_exige_60_minutos_y_conserva_reserva_original(escenario):
    usuario, bloques, ahora = escenario
    horario_original = Horario.objects.create(
        hora_inicio=time(14), hora_fin=time(16)
    )
    horario_destino = Horario.objects.create(
        hora_inicio=time(16, 15), hora_fin=time(18, 15)
    )
    original = SalaHorario.objects.create(
        sala=bloques[0].sala, horario=horario_original
    )
    destino = SalaHorario.objects.create(
        sala=bloques[0].sala, horario=horario_destino
    )
    reserva = Reserva.objects.create(
        usuario=usuario,
        sala_horario=original,
        fecha=ahora.date(),
        tipo_actividad="Tarea",
    )

    a_las_1315 = ahora.replace(hour=13, minute=15)
    with patch("reservas.services.timezone.localtime", return_value=a_las_1315):
        with pytest.raises(services.ReservationError, match="60 minutos"):
            services.modify_student_reservation(
                usuario.pk, reserva.pk, destino.pk
            )

    reserva.refresh_from_db()
    assert reserva.sala_horario == original
    assert reserva.estado_reserva == Reserva.ESTADO_CONFIRMADA

    exactamente_una_hora_antes = ahora.replace(hour=13, minute=0)
    with patch(
        "reservas.services.timezone.localtime",
        return_value=exactamente_una_hora_antes,
    ):
        services.modify_student_reservation(
            usuario.pk, reserva.pk, destino.pk
        )
    reserva.refresh_from_db()
    assert reserva.sala_horario == destino


def test_destino_ocupado_no_libera_la_reserva_original(escenario):
    usuario, bloques, ahora = escenario
    reserva = services.create_student_reservation(
        usuario.pk, bloques[0].pk, "Tarea"
    )
    sala_b = Sala.objects.create(nombre_sala="Sala B")
    destino = SalaHorario.objects.create(
        sala=sala_b, horario=bloques[0].horario
    )
    otro = Usuario.objects.create(
        rol=Rol.objects.get_or_create(nombre_rol="Solicitante")[0],
        pk=94186, email="otro@test.edu", nombre="Otro", apellido="Test"
    )
    Reserva.objects.create(
        usuario=otro,
        sala_horario=destino,
        fecha=ahora.date(),
        tipo_actividad="Examen",
    )

    with pytest.raises(services.ReservationError, match="otro usuario"):
        services.modify_student_reservation(
            usuario.pk, reserva.pk, destino.pk
        )

    reserva.refresh_from_db()
    assert reserva.sala_horario == bloques[0]
    assert reserva.estado_reserva == Reserva.ESTADO_CONFIRMADA


def test_modificacion_respeta_bloques_consecutivos(escenario):
    usuario, bloques, ahora = escenario
    reserva = services.create_student_reservation(
        usuario.pk, bloques[0].pk, "Tarea"
    )
    Reserva.objects.create(
        usuario=usuario,
        sala_horario=bloques[2],
        fecha=ahora.date(),
        tipo_actividad="Proyecto",
    )

    with pytest.raises(services.ReservationError, match="consecutivo"):
        services.modify_student_reservation(
            usuario.pk, reserva.pk, bloques[1].pk
        )

    reserva.refresh_from_db()
    assert reserva.sala_horario == bloques[0]


def test_no_se_puede_modificar_una_reserva_ajena(escenario):
    usuario, bloques, ahora = escenario
    reserva = services.create_student_reservation(
        usuario.pk, bloques[0].pk, "Tarea"
    )
    otro = Usuario.objects.create(
        rol=Rol.objects.get(nombre_rol="Solicitante"),
        pk=94186,
        email="otro@test.edu",
        nombre="Otro",
        apellido="Test",
        password_hash=make_password("clave-segura"),
    )
    destino = SalaHorario.objects.create(
        sala=Sala.objects.create(nombre_sala="Sala B"),
        horario=bloques[0].horario,
    )

    with pytest.raises(services.ReservationError, match="no te pertenece"):
        services.modify_student_reservation(
            otro.pk, reserva.pk, destino.pk
        )

    reserva.refresh_from_db()
    assert reserva.usuario == usuario
    assert reserva.sala_horario == bloques[0]
