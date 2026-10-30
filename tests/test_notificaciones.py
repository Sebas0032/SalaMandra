from datetime import datetime, time, timedelta
from unittest.mock import patch

import pytest
from django.contrib.auth.hashers import make_password
from django.urls import reverse
from django.utils import timezone

from reservas import services
from reservas.models import Horario, Notificacion, Reserva, Rol, Sala, SalaHorario, Usuario


pytestmark = pytest.mark.django_db


@pytest.fixture
def escenario_notificaciones(client):
    ahora = timezone.make_aware(datetime(2026, 10, 28, 8, 0))
    solicitante = Usuario.objects.create(
        pk=101145,
        rol=Rol.objects.get_or_create(nombre_rol=Rol.Nombre.SOLICITANTE)[0],
        email="sebastian@upb.edu",
        nombre="Sebastian",
        apellido="Cruz",
        password_hash=make_password("clave"),
    )
    admin = Usuario.objects.create(
        pk=900001,
        rol=Rol.objects.get_or_create(nombre_rol=Rol.Nombre.ADMINISTRADOR)[0],
        email="admin@upb.edu",
        nombre="Admin",
        apellido="SalaMandra",
        password_hash=make_password("clave-admin"),
    )
    operante = Usuario.objects.create(
        pk=900002,
        rol=Rol.objects.get_or_create(nombre_rol=Rol.Nombre.OPERANTE)[0],
        email="operante@upb.edu",
        nombre="Operante",
        apellido="SalaMandra",
        password_hash=make_password("clave-operante"),
    )
    horario = Horario.objects.create(hora_inicio=time(14), hora_fin=time(16))
    sala_horario = SalaHorario.objects.create(
        sala=Sala.objects.create(nombre_sala="Sala A"),
        horario=horario,
    )
    reserva = Reserva.objects.create(
        usuario=solicitante,
        sala_horario=sala_horario,
        fecha=ahora.date(),
        tipo_actividad="Tarea",
    )
    client.post(
        reverse("login"),
        {"identificador": str(solicitante.pk), "password": "clave"},
    )
    return solicitante, admin, operante, sala_horario, reserva, ahora


def test_mantenimiento_crea_aviso_persistente(escenario_notificaciones):
    solicitante, admin, _, sala_horario, reserva, ahora = escenario_notificaciones

    with patch("reservas.services.timezone.localtime", return_value=ahora):
        services.block_room_schedule_for_maintenance(
            admin.pk, sala_horario.pk, "Fuga de agua"
        )

    aviso = Notificacion.objects.get()
    assert aviso.usuario == solicitante
    assert aviso.actor == admin
    assert aviso.reserva == reserva
    assert aviso.tipo == Notificacion.Tipo.MANTENIMIENTO
    assert "Fuga de agua" in aviso.mensaje
    assert aviso.leida is False


def test_cancelacion_de_gestion_notifica_al_titular(escenario_notificaciones):
    solicitante, admin, _, _, reserva, ahora = escenario_notificaciones

    with patch("reservas.services.timezone.localtime", return_value=ahora):
        services.cancel_reservation(admin.pk, reserva.pk)

    aviso = Notificacion.objects.get()
    assert aviso.usuario == solicitante
    assert aviso.actor == admin
    assert aviso.tipo == Notificacion.Tipo.CANCELACION_GESTION
    assert Rol.Nombre.ADMINISTRADOR in aviso.mensaje


def test_cancelacion_propia_no_crea_aviso(escenario_notificaciones):
    solicitante, _, _, _, reserva, ahora = escenario_notificaciones

    with patch("reservas.services.timezone.localtime", return_value=ahora):
        services.cancel_reservation(solicitante.pk, reserva.pk)

    assert not Notificacion.objects.exists()


@pytest.mark.integration
def test_modificacion_de_gestion_notifica_origen_y_destino(
    escenario_notificaciones,
):
    solicitante, admin, _, sala_horario, reserva, ahora = escenario_notificaciones
    destino = SalaHorario.objects.create(
        sala=Sala.objects.create(nombre_sala="Sala B"),
        horario=sala_horario.horario,
    )

    with patch("reservas.services.timezone.localtime", return_value=ahora):
        services.modify_reservation(admin.pk, reserva.pk, destino.pk)

    aviso = Notificacion.objects.get()
    assert aviso.usuario == solicitante
    assert aviso.actor == admin
    assert aviso.tipo == Notificacion.Tipo.MODIFICACION_GESTION
    assert "Sala A" in aviso.mensaje
    assert "Sala B" in aviso.mensaje


def test_cada_modificacion_de_gestion_conserva_su_notificacion(
    escenario_notificaciones,
):
    _, admin, _, sala_horario, reserva, ahora = escenario_notificaciones
    destinos = [
        SalaHorario.objects.create(
            sala=Sala.objects.create(nombre_sala=nombre),
            horario=sala_horario.horario,
        )
        for nombre in ("Sala B", "Sala C")
    ]

    with patch("reservas.services.timezone.localtime", return_value=ahora):
        services.modify_reservation(admin.pk, reserva.pk, destinos[0].pk)
        services.modify_reservation(admin.pk, reserva.pk, destinos[1].pk)

    assert Notificacion.objects.filter(
        reserva=reserva,
        tipo=Notificacion.Tipo.MODIFICACION_GESTION,
    ).count() == 2


def test_panel_muestra_aviso_y_permite_marcarlo_como_leido(
    client, escenario_notificaciones
):
    solicitante, admin, _, _, reserva, ahora = escenario_notificaciones
    aviso = Notificacion.objects.create(
        usuario=solicitante,
        reserva=reserva,
        actor=admin,
        tipo=Notificacion.Tipo.CANCELACION_GESTION,
        mensaje="Tu reserva fue cancelada por un Administrador.",
        fecha=ahora,
    )

    with patch("reservas.services.timezone.localtime", return_value=ahora):
        panel = client.get(reverse("student_panel"))
    assert panel.status_code == 200
    assert "Tu reserva fue cancelada" in panel.content.decode()
    assert "Entendido" in panel.content.decode()

    response = client.post(reverse("mark_notification_read", args=[aviso.pk]))
    assert response.url == reverse("student_panel")
    aviso.refresh_from_db()
    assert aviso.leida is True
    assert Notificacion.objects.filter(pk=aviso.pk).exists()
    with patch("reservas.services.timezone.localtime", return_value=ahora):
        panel = client.get(reverse("student_panel"))
    assert "Tu reserva fue cancelada" not in panel.content.decode()


def test_estudiante_no_puede_marcar_aviso_ajeno(
    client, escenario_notificaciones
):
    _, admin, _, _, reserva, ahora = escenario_notificaciones
    otro = Usuario.objects.create(
        pk=94186,
        rol=Rol.objects.get(nombre_rol=Rol.Nombre.SOLICITANTE),
        email="otro@upb.edu",
        nombre="Otro",
        apellido="Estudiante",
    )
    aviso = Notificacion.objects.create(
        usuario=otro,
        reserva=reserva,
        actor=admin,
        tipo=Notificacion.Tipo.CANCELACION_GESTION,
        mensaje="Aviso ajeno",
        fecha=ahora + timedelta(minutes=1),
    )

    client.post(reverse("mark_notification_read", args=[aviso.pk]))
    aviso.refresh_from_db()
    assert aviso.leida is False
