from datetime import datetime, time, timedelta
from unittest.mock import patch

import pytest
from django.contrib.auth.hashers import make_password
from django.urls import reverse
from django.utils import timezone

from reservas import services
from reservas.models import (
    Auditoria,
    Horario,
    Notificacion,
    Reserva,
    Rol,
    Sala,
    SalaHorario,
    Sancion,
    TipoSancion,
    Usuario,
)


pytestmark = pytest.mark.django_db


@pytest.fixture
def escenario_cancelacion(client):
    ahora = timezone.make_aware(datetime(2026, 10, 19, 13))
    usuario = Usuario.objects.create(
        rol=Rol.objects.get_or_create(nombre_rol="Solicitante")[0],
        pk=95429,
        email="95429@salamandra.test",
        nombre="Luciana",
        apellido="Soledad",
        password_hash=make_password("clave"),
    )
    horario = Horario.objects.create(hora_inicio=time(14), hora_fin=time(16))
    bloque = SalaHorario.objects.create(
        sala=Sala.objects.create(nombre_sala="Sala A"), horario=horario
    )
    reserva = Reserva.objects.create(
        usuario=usuario,
        sala_horario=bloque,
        fecha=ahora.date(),
        tipo_actividad="Tarea",
    )
    client.post(
        reverse("login"),
        {"identificador": str(usuario.pk), "password": "clave"},
    )
    return usuario, bloque, reserva, ahora


# Test 11: verifica la cancelación exacta a 60 minutos sin sanción.
def test_cancela_exactamente_60_minutos_antes_sin_sancion(
    escenario_cancelacion,
):
    usuario, bloque, reserva, ahora = escenario_cancelacion
    with patch("reservas.services.timezone.localtime", return_value=ahora):
        resultado = services.cancel_reservation(usuario.pk, reserva.pk)

    reserva.refresh_from_db()
    assert reserva.estado_reserva == Reserva.ESTADO_CANCELADA
    assert resultado["sancion"] is None
    assert not Sancion.objects.exists()

    with patch("reservas.services.timezone.localtime", return_value=ahora):
        nueva = services.create_student_reservation(usuario.pk, bloque.pk, "Tarea")
    assert nueva.estado_reserva == Reserva.ESTADO_CONFIRMADA


@pytest.mark.parametrize(
    ("faltas_previas", "tipo_esperado", "duracion_esperada"),
    [
        (0, TipoSancion.ID_24_HORAS, 24),
        (2, TipoSancion.ID_1_SEMANA, 168),
        (3, TipoSancion.ID_SEMESTRE, None),
    ],
)
# Tests 12-14: verifican la escala de sanciones por faltas acumuladas.
def test_cancelacion_tardia_aplica_sancion_escalar(
    escenario_cancelacion, faltas_previas, tipo_esperado, duracion_esperada
):
    usuario, _, reserva, ahora = escenario_cancelacion
    ahora = ahora.replace(hour=13, minute=30)
    for indice in range(faltas_previas):
        nombre, tipo_id = services.ESCALA_SANCIONES_CANCELACION[indice]
        tipo = TipoSancion.objects.get(pk=tipo_id)
        Sancion.objects.create(
        origen=Sancion.Origen.AUTOMATICA,
            usuario=usuario,
            tipo_sancion=tipo,
            motivo=nombre,
            fecha_inicio=ahora - timedelta(days=10),
            fecha_fin=ahora - timedelta(days=9),
        )

    with patch("reservas.services.timezone.localtime", return_value=ahora):
        resultado = services.cancel_reservation(usuario.pk, reserva.pk)

    sancion = resultado["sancion"]
    assert sancion.origen == Sancion.Origen.AUTOMATICA
    assert sancion.aplicada_por_id is None
    assert sancion.tipo_sancion_id == tipo_esperado
    assert sancion.tipo_sancion.duracion == duracion_esperada
    if tipo_esperado == TipoSancion.ID_SEMESTRE:
        assert sancion.fecha_fin == timezone.make_aware(datetime(2027, 1, 1))
    else:
        assert sancion.fecha_fin == ahora + timedelta(hours=duracion_esperada)
    assert Sancion.objects.filter(usuario=usuario).count() == faltas_previas + 1
    reserva.refresh_from_db()
    assert reserva.estado_reserva == Reserva.ESTADO_CANCELADA


# Test 15: verifica que una reserva iniciada no pueda cancelarse.
def test_no_cancela_una_reserva_que_ya_comenzo(escenario_cancelacion):
    usuario, _, reserva, ahora = escenario_cancelacion
    ahora = ahora.replace(hour=14)
    with patch("reservas.services.timezone.localtime", return_value=ahora):
        with pytest.raises(services.ReservationError, match="ya comenzó"):
            services.cancel_reservation(usuario.pk, reserva.pk)

    reserva.refresh_from_db()
    assert reserva.estado_reserva == Reserva.ESTADO_CONFIRMADA
    assert not Sancion.objects.exists()


# Test 16: verifica que no se cancelen reservas ajenas.
def test_solicitante_no_puede_cancelar_reserva_ajena(escenario_cancelacion):
    _, _, reserva, ahora = escenario_cancelacion
    otro = Usuario.objects.create(
        rol=Rol.objects.get(nombre_rol="Solicitante"),
        pk=94186,
        email="otro@salamandra.test",
        nombre="Otro",
        apellido="Usuario",
        password_hash=make_password("clave"),
    )

    with patch("reservas.services.timezone.localtime", return_value=ahora):
        with pytest.raises(services.ReservationError, match="no te pertenece"):
            services.cancel_reservation(otro.pk, reserva.pk)
    reserva.refresh_from_db()
    assert reserva.estado_reserva == Reserva.ESTADO_CONFIRMADA


@pytest.mark.integration
# Test 17: verifica que el Operante cancele sin sancionar y notifique.
def test_operador_cancela_sin_sancionar_y_notifica_al_titular(
    escenario_cancelacion,
):
    usuario, _, reserva, ahora = escenario_cancelacion
    ahora = ahora.replace(hour=13, minute=30)
    operador = Usuario.objects.create(
        rol=Rol.objects.get_or_create(nombre_rol="Operante")[0],
        pk=900002,
        email="operador@salamandra.test",
        nombre="Operador",
        apellido="Prueba",
        password_hash=make_password("clave"),
    )

    with patch("reservas.services.timezone.localtime", return_value=ahora):
        resultado = services.cancel_reservation(operador.pk, reserva.pk)
    reserva.refresh_from_db()
    assert reserva.usuario == usuario
    assert reserva.estado_reserva == Reserva.ESTADO_CANCELADA
    assert resultado["sancion"] is None
    assert not Sancion.objects.exists()
    aviso = Notificacion.objects.get(reserva=reserva)
    assert aviso.usuario == usuario
    assert aviso.actor == operador


# Test 18: verifica el resultado mostrado por el panel al cancelar.
def test_cancelacion_desde_el_panel_muestra_resultado(
    client, escenario_cancelacion
):
    _, _, reserva, ahora = escenario_cancelacion
    ahora = ahora.replace(minute=30)
    with patch("reservas.services.timezone.localtime", return_value=ahora):
        panel = client.get(reverse("student_panel"))
        assert reverse("cancel_reservation", args=[reserva.pk]) in panel.content.decode()
        assert "vas a recibir una sanción" in panel.content.decode()
        respuesta = client.post(
            reverse("cancel_reservation", args=[reserva.pk]), follow=True
        )

    assert respuesta.status_code == 200
    assert "Se aplicó" in respuesta.content.decode()
    reserva.refresh_from_db()
    assert reserva.estado_reserva == Reserva.ESTADO_CANCELADA


# Test 19: verifica la cancelación administrativa sin sanción.
def test_administrador_lista_y_cancela_reservas_sin_sancion(
    client, escenario_cancelacion
):
    usuario, bloque, reserva, ahora = escenario_cancelacion
    ahora = ahora.replace(minute=30)
    admin = Usuario.objects.create(
        rol=Rol.objects.get_or_create(nombre_rol="Administrador")[0],
        pk=900001,
        email="admin@salamandra.test",
        nombre="Admin",
        apellido="Prueba",
        password_hash=make_password("clave-admin"),
    )
    horario_pasado = Horario.objects.create(
        hora_inicio=time(11), hora_fin=time(13)
    )
    bloque_pasado = SalaHorario.objects.create(
        sala=bloque.sala, horario=horario_pasado
    )
    reserva_iniciada = Reserva.objects.create(
        usuario=usuario,
        sala_horario=bloque_pasado,
        fecha=ahora.date(),
        tipo_actividad="Lectura",
    )
    client.get(reverse("logout"))
    client.post(
        reverse("login"),
        {"identificador": str(admin.pk), "password": "clave-admin"},
    )

    with patch("reservas.services.timezone.localtime", return_value=ahora):
        panel = client.get(reverse("admin_cancellations"))
        assert reverse("admin_cancel_reservation", args=[reserva.pk]) in panel.content.decode()
        assert reverse(
            "admin_cancel_reservation", args=[reserva_iniciada.pk]
        ) in panel.content.decode()
        respuesta = client.post(
            reverse("admin_cancel_reservation", args=[reserva.pk]), follow=True
        )

    assert respuesta.status_code == 200
    reserva.refresh_from_db()
    assert reserva.estado_reserva == Reserva.ESTADO_CANCELADA
    assert not Sancion.objects.exists()
    assert Auditoria.objects.get(
        reserva=reserva, accion=Auditoria.Accion.CANCELAR
    ).actor == admin
