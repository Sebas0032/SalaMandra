from datetime import datetime, time
from unittest.mock import patch

import pytest
from django.contrib.auth.hashers import make_password
from django.urls import reverse
from django.utils import timezone

from reservas import services
from reservas.models import (
    Auditoria, Desbloqueo, Horario, Notificacion, Reserva, Rol, Sala,
    SalaHorario, Sancion,
    Usuario,
)


pytestmark = pytest.mark.django_db


@pytest.fixture
def escenario_operante(client):
    operante, _ = Usuario.objects.update_or_create(
        pk=900003,
        defaults={
            "rol": Rol.objects.get_or_create(nombre_rol="Operante")[0],
            "email": "operante@test.edu",
            "nombre": "Omar",
            "apellido": "Operante",
            "password_hash": make_password("Operante_2026!"),
        },
    )
    solicitante = Usuario.objects.create(
        pk=2024001234,
        rol=Rol.objects.get_or_create(nombre_rol="Solicitante")[0],
        email="matheo@test.edu",
        nombre="Matheo",
        apellido="Oliva",
    )
    horario_a = Horario.objects.create(hora_inicio=time(14), hora_fin=time(16))
    horario_b = Horario.objects.create(hora_inicio=time(16, 15), hora_fin=time(18, 15))
    bloques = [
        SalaHorario.objects.create(
            sala=Sala.objects.create(nombre_sala=nombre), horario=horario
        )
        for nombre, horario in (("Sala C", horario_a), ("Sala F", horario_b))
    ]
    client.post(
        reverse("login"),
        {"identificador": str(operante.pk), "password": "Operante_2026!"},
    )
    ahora = timezone.make_aware(datetime(2026, 10, 28, 9))
    with patch("reservas.services.timezone.localtime", return_value=ahora):
        yield operante, solicitante, bloques, ahora


def test_login_operante_llega_a_su_panel(client, escenario_operante):
    response = client.get(reverse("dashboard"))
    assert response.url == reverse("operator_panel")
    panel = client.get(reverse("operator_panel"))
    assert panel.status_code == 200
    contenido = panel.content.decode()
    assert "Operante" in contenido
    assert "Sanciones" not in contenido
    assert "Crear horario" not in contenido


def test_panel_renderiza_cada_apartado(client, escenario_operante):
    _, solicitante, bloques, _ = escenario_operante
    apartados = [
        ("reservar", "Reservar para un solicitante"),
        ("modificar", "Modificar una reserva"),
        ("cancelar", "Cancelar una reserva"),
        ("mantenimiento", "Mantenimiento"),
    ]
    for accion, titulo in apartados:
        parametros = {"accion": accion}
        if accion != "mantenimiento":
            parametros["codigo"] = solicitante.pk
        response = client.get(reverse("operator_panel"), parametros)
        assert response.status_code == 200
        assert titulo in response.content.decode()

        if accion in {"modificar", "cancelar"}:
            reserva = Reserva.objects.create(
                usuario=solicitante,
                sala_horario=bloques[0],
                fecha=timezone.localdate(),
                tipo_actividad="Tarea",
            )
            response = client.get(
                reverse("operator_panel"),
                {
                    "accion": accion,
                    "codigo": solicitante.pk,
                    "reserva": reserva.pk,
                },
            )
            assert response.status_code == 200
            assert f'value="{reserva.pk}"' in response.content.decode()
            reserva.delete()


def test_operante_reserva_para_solicitante_y_audita_actor(client, escenario_operante):
    operante, solicitante, bloques, _ = escenario_operante
    response = client.post(
        reverse("operator_panel"),
        {
            "accion": "reservar",
            "codigo_solicitante": solicitante.pk,
            "id_sala_horario": bloques[0].pk,
            "actividad": "Tarea",
        },
    )
    assert response.status_code == 302
    reserva = Reserva.objects.get()
    auditoria = Auditoria.objects.get(reserva=reserva)
    assert reserva.usuario == solicitante
    assert auditoria.actor == operante
    assert auditoria.accion == Auditoria.Accion.CREAR


@pytest.mark.e2e
def test_operante_modifica_y_cancela_reserva_ajena(client, escenario_operante):
    operante, solicitante, bloques, ahora = escenario_operante
    reserva = services.create_reservation(
        operante.pk, solicitante.pk, bloques[0].pk, "Proyecto"
    )
    client.post(
        reverse("operator_panel"),
        {
            "accion": "modificar",
            "codigo_solicitante": solicitante.pk,
            "id_reserva": reserva.pk,
            "id_sala_horario": bloques[1].pk,
        },
    )
    reserva.refresh_from_db()
    assert reserva.usuario == solicitante
    assert reserva.sala_horario == bloques[1]
    assert reserva.auditorias.get(accion="MODIFICAR").actor == operante

    with patch(
        "reservas.services.timezone.localtime",
        return_value=ahora.replace(hour=15, minute=30),
    ):
        client.post(
            reverse("operator_panel"),
            {
                "accion": "cancelar",
                "codigo_solicitante": solicitante.pk,
                "id_reserva": reserva.pk,
            },
        )
    reserva.refresh_from_db()
    assert reserva.estado_reserva == Reserva.ESTADO_CANCELADA
    assert reserva.auditorias.get(accion="CANCELAR").actor == operante
    assert not Sancion.objects.exists()
    assert Notificacion.objects.get(
        reserva=reserva,
        tipo=Notificacion.Tipo.CANCELACION_GESTION,
    ).usuario == solicitante


def test_operante_gestiona_mantenimiento_sin_sancionar(client, escenario_operante):
    operante, solicitante, bloques, _ = escenario_operante
    reserva = services.create_reservation(
        operante.pk, solicitante.pk, bloques[0].pk, "Examen"
    )
    response = client.post(
        reverse("operator_panel"),
        {
            "accion": "mantenimiento",
            "id_sala_horario": bloques[0].pk,
            "motivo": "Revisión eléctrica",
        },
    )
    assert response.status_code == 302
    reserva.refresh_from_db()
    assert reserva.estado_reserva == Reserva.ESTADO_POR_MANTENIMIENTO
    assert reserva.auditorias.get(accion="CANCELAR").actor == operante
    assert not Sancion.objects.exists()
    assert client.post(
        reverse("operator_unblock_room", args=[bloques[0].pk])
    ).status_code == 302
    bloques[0].refresh_from_db()
    assert bloques[0].estado_sala_horario == SalaHorario.ESTADO_DISPONIBLE
    assert Desbloqueo.objects.get().desbloqueado_por == operante


def test_operante_no_accede_a_sanciones_ni_gestion_de_horarios(client, escenario_operante):
    assert client.get(reverse("sanctions_admin")).status_code == 403
    assert client.post(reverse("apply_sanction"), {}).status_code == 403
    assert client.get(reverse("gestion_salas")).status_code == 403


def test_solicitante_no_accede_al_panel_operante(client, escenario_operante):
    _, solicitante, _, _ = escenario_operante
    solicitante.password_hash = make_password("clave-segura")
    solicitante.save(update_fields=["password_hash"])
    client.get(reverse("logout"))
    client.post(
        reverse("login"),
        {"identificador": str(solicitante.pk), "password": "clave-segura"},
    )
    assert client.get(reverse("operator_panel")).status_code == 403
