from datetime import time
from io import StringIO

import pytest
from django.contrib.auth.hashers import check_password
from django.core.management import call_command

from cuentas.services import register_student_account
from reservas.models import (
    Bloqueo,
    Desbloqueo,
    Horario,
    Notificacion,
    ReinicioSanciones,
    Reserva,
    Sala,
    SalaHorario,
    Usuario,
)


pytestmark = pytest.mark.integration


@pytest.mark.django_db
# Test 79: verifica la carga inicial de salas y horarios sin duplicados.
def test_seed_data_carga_seis_salas_con_seis_horarios_sin_duplicar():
    horarios_esperados = {
        (time(7, 45), time(9, 45)),
        (time(10, 0), time(12, 0)),
        (time(12, 15), time(14, 15)),
        (time(14, 30), time(16, 30)),
        (time(16, 45), time(18, 45)),
        (time(19, 0), time(21, 0)),
    }

    call_command("seed_data", stdout=StringIO())
    call_command("seed_data", stdout=StringIO())

    assert set(Sala.objects.values_list("nombre_sala", flat=True)) == {
        f"Sala de estudio {letra}" for letra in "ABCDEF"
    }
    assert set(Horario.objects.values_list("hora_inicio", "hora_fin")) == horarios_esperados
    assert SalaHorario.objects.count() == 36
    for sala in Sala.objects.all():
        assert set(
            SalaHorario.objects.filter(sala=sala).values_list(
                "horario__hora_inicio", "horario__hora_fin"
            )
        ) == horarios_esperados
    assert Reserva.objects.count() == 2


@pytest.mark.django_db
# Test 80: verifica la precarga sin reemplazar cuentas registradas.
def test_seed_data_precarga_los_16_alumnos_y_no_reemplaza_cuentas_registradas():
    alumnos_esperados = {
        (95445, "95445@salamandra.test", "Santiago", "Arauz"),
        (94186, "94186@salamandra.test", "Sofía", "Arduz"),
        (94102, "94102@salamandra.test", "Gonzalo", "Cardenas"),
        (101145, "101145@salamandra.test", "Sebastian", "Cruz"),
        (87097, "87097@salamandra.test", "Ismael", "Diaz"),
        (86289, "86289@salamandra.test", "Marcos", "Dominguez"),
        (89352, "89352@salamandra.test", "Andrew", "Laura"),
        (94635, "94635@salamandra.test", "Katrina", "Leigue"),
        (91870, "91870@salamandra.test", "Alejandro", "Parraga"),
        (95429, "95429@salamandra.test", "Luciana", "Soledad"),
        (94008, "94008@salamandra.test", "Sebastian", "Soto"),
        (94302, "94302@salamandra.test", "Peter", "Teran"),
        (94046, "94046@salamandra.test", "Andrea", "Trujillo"),
        (95187, "95187@salamandra.test", "Raul", "Vaca"),
        (95503, "95503@salamandra.test", "Hugo", "Zuñiga"),
        (95343, "95343@salamandra.test", "Lucas", "Leibovich"),
    }

    call_command("seed_data", stdout=StringIO())

    alumnos = Usuario.objects.filter(rol__nombre_rol="Solicitante")
    assert set(alumnos.values_list("codigo_usuario", "email", "nombre", "apellido")) == alumnos_esperados
    assert alumnos.filter(estado_usuario=True, password_hash="").count() == 16
    assert set(Reserva.objects.values_list("usuario_id", flat=True)) == {95429}

    register_student_account(101145, "101145@salamandra.test", "ClaveSegura2026!")
    call_command("seed_data", stdout=StringIO())

    usuario = Usuario.objects.get(pk=101145)
    assert check_password("ClaveSegura2026!", usuario.password_hash)
    assert Usuario.objects.count() == 18  # Administrador, Operante y 16 alumnos.


@pytest.mark.django_db
# Test 81: verifica el reinicio de datos con el historial actual.
def test_seed_data_reset_funciona_con_todo_el_historial_nuevo():
    call_command("seed_data", stdout=StringIO())
    admin = Usuario.objects.get(pk=900001)
    reserva = Reserva.objects.first()
    bloqueo = Bloqueo.objects.create(
        usuario=admin,
        sala_horario=reserva.sala_horario,
        motivo="Prueba de reinicio",
    )
    Desbloqueo.objects.create(bloqueo=bloqueo, desbloqueado_por=admin)
    Notificacion.objects.create(
        usuario=reserva.usuario,
        reserva=reserva,
        actor=admin,
        tipo=Notificacion.Tipo.CANCELACION_GESTION,
        mensaje="Prueba",
    )
    ReinicioSanciones.objects.create(administrador=admin)

    call_command("seed_data", reset=True, stdout=StringIO())

    assert Notificacion.objects.count() == 0
    assert Bloqueo.objects.count() == 0
    assert Desbloqueo.objects.count() == 0
    assert ReinicioSanciones.objects.count() == 0
    assert Sala.objects.count() == 6
    assert Horario.objects.count() == 6
    assert SalaHorario.objects.count() == 36
    assert Reserva.objects.count() == 2
