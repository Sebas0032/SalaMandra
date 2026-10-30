from datetime import datetime, time, timedelta
from unittest.mock import patch

import pytest
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.utils import timezone

from cuentas.services import RegistrationError, register_student_account, usuario_tiene_rol
from reservas import gestion_sanciones, services
from reservas.models import Auditoria, Horario, Reserva, Rol, Sala, SalaHorario, Sancion, TipoSancion, Usuario


pytestmark = pytest.mark.django_db


@pytest.fixture
def escenario_auditoria():
    solicitante = Usuario.objects.create(
        pk=10, rol=Rol.objects.get_or_create(nombre_rol="Solicitante")[0],
        email="ana@test.edu", nombre="Ana", apellido="Prueba", password_hash="registrada",
    )
    admin = Usuario.objects.create(
        pk=25, rol=Rol.objects.get_or_create(nombre_rol="Administrador")[0],
        email="admin@test.edu", nombre="Admin", apellido="Prueba", password_hash="registrada",
    )
    horario = Horario.objects.create(hora_inicio=time(14), hora_fin=time(16))
    bloques = [
        SalaHorario.objects.create(sala=Sala.objects.create(nombre_sala=nombre), horario=horario)
        for nombre in ("A", "B")
    ]
    ahora = timezone.make_aware(datetime(2026, 10, 28, 9))
    with patch("reservas.services.timezone.localtime", return_value=ahora):
        yield solicitante, admin, bloques, ahora


def test_historial_crear_modificar_cancelar_conserva_titular(escenario_auditoria):
    ana, admin, bloques, ahora = escenario_auditoria
    reserva = services.create_student_reservation(ana.pk, bloques[0].pk, "Tarea")
    services.modify_student_reservation(ana.pk, reserva.pk, bloques[1].pk)
    services.cancel_reservation(admin.pk, reserva.pk)
    reserva.refresh_from_db()
    assert reserva.usuario == ana
    assert reserva.sala_horario == bloques[1]
    assert reserva.estado_reserva == Reserva.ESTADO_CANCELADA
    assert list(reserva.auditorias.values_list("actor_id", "accion", "fecha_accion")) == [
        (ana.pk, "CREAR", ahora), (ana.pk, "MODIFICAR", ahora), (admin.pk, "CANCELAR", ahora),
    ]


@pytest.mark.integration
def test_fallo_auditoria_revierte_operacion_y_sancion(escenario_auditoria):
    ana, _, bloques, ahora = escenario_auditoria
    for accion in ("CREAR", "MODIFICAR", "CANCELAR"):
        Reserva.objects.all().delete()
        Sancion.objects.all().delete()
        reserva = None
        if accion != "CREAR":
            reserva = services.create_student_reservation(
                ana.pk, bloques[0].pk, "Tarea"
            )

        with patch(
            "reservas.services.Auditoria.objects.create",
            side_effect=RuntimeError("fallo"),
        ):
            with pytest.raises(RuntimeError, match="fallo"):
                if accion == "CREAR":
                    services.create_student_reservation(
                        ana.pk, bloques[0].pk, "Tarea"
                    )
                elif accion == "MODIFICAR":
                    services.modify_student_reservation(
                        ana.pk, reserva.pk, bloques[1].pk
                    )
                else:
                    with patch(
                        "reservas.services.timezone.localtime",
                        return_value=ahora.replace(hour=13, minute=30),
                    ):
                        services.cancel_reservation(ana.pk, reserva.pk)

        assert not Sancion.objects.exists()
        if reserva is None:
            assert not Reserva.objects.exists()
            assert not Auditoria.objects.exists()
        else:
            reserva.refresh_from_db()
            assert reserva.estado_reserva == Reserva.ESTADO_CONFIRMADA
            assert reserva.sala_horario == bloques[0]
            assert list(
                reserva.auditorias.values_list("accion", flat=True)
            ) == ["CREAR"]


def test_cancelacion_repetida_no_duplica_historial_ni_sancion(escenario_auditoria):
    ana, _, bloques, ahora = escenario_auditoria
    reserva = services.create_student_reservation(ana.pk, bloques[0].pk, "Tarea")
    with patch("reservas.services.timezone.localtime", return_value=ahora.replace(hour=13, minute=30)):
        services.cancel_reservation(ana.pk, reserva.pk)
        with pytest.raises(services.ReservationError):
            services.cancel_reservation(ana.pk, reserva.pk)
    assert reserva.auditorias.filter(accion="CANCELAR").count() == 1
    assert Sancion.objects.count() == 1


def test_mantenimiento_registra_administrador_y_no_sanciona(escenario_auditoria):
    ana, admin, bloques, _ = escenario_auditoria
    reserva = services.create_student_reservation(ana.pk, bloques[0].pk, "Tarea")
    services.block_room_schedule_for_maintenance(admin.pk, bloques[0].pk, "Reparación")
    assert reserva.auditorias.get(accion="CANCELAR").actor == admin
    assert not Sancion.objects.exists()


def test_solicitante_no_puede_sancionar_manualmente(escenario_auditoria):
    ana, admin, _, _ = escenario_auditoria
    with pytest.raises(gestion_sanciones.GestionSancionesError):
        gestion_sanciones.apply_manual_sanction(ana.pk, admin.pk, "24_horas", "Motivo")
    assert not Sancion.objects.exists()


def test_bd_rechaza_origen_aplicador_incoherentes(escenario_auditoria):
    ana, admin, _, ahora = escenario_auditoria
    tipo = TipoSancion.objects.get(pk=TipoSancion.ID_24_HORAS)
    casos_invalidos = (
        ("MANUAL", False),
        ("AUTOMATICA", True),
        ("OTRO", False),
    )
    for origen, con_actor in casos_invalidos:
        with pytest.raises(IntegrityError), transaction.atomic():
            Sancion.objects.create(
                usuario=ana,
                tipo_sancion=tipo,
                origen=origen,
                aplicada_por=admin if con_actor else None,
                motivo="Motivo",
                fecha_inicio=ahora,
                fecha_fin=ahora + timedelta(hours=24),
            )


def test_modelo_valida_rol_del_aplicador(escenario_auditoria):
    ana, _, _, ahora = escenario_auditoria
    tipo = TipoSancion.objects.get(pk=TipoSancion.ID_24_HORAS)
    sancion = Sancion(
        usuario=ana, aplicada_por=ana, origen="MANUAL", tipo_sancion=tipo,
        motivo="Motivo", fecha_inicio=ahora, fecha_fin=ahora + timedelta(hours=24),
    )
    with pytest.raises(ValidationError, match="administrador"):
        sancion.full_clean()


def test_rol_unico_y_catalogo_restringido(escenario_auditoria):
    ana, _, _, _ = escenario_auditoria
    ana.rol = Rol.objects.get_or_create(nombre_rol="Operante")[0]
    ana.save(update_fields=["rol"])
    assert usuario_tiene_rol(ana.pk, "Operante")
    assert not usuario_tiene_rol(ana.pk, "Solicitante")
    with pytest.raises(IntegrityError), transaction.atomic():
        Usuario.objects.filter(pk=ana.pk).update(rol=None)
    for nombre in ("Solicitante", "Estudiante", "Operador", "Otro"):
        with pytest.raises(IntegrityError), transaction.atomic():
            Rol.objects.create(nombre_rol=nombre)
    assert set(TipoSancion.objects.values_list("pk", flat=True)) == {74, 75, 76, 77}
    with pytest.raises(IntegrityError), transaction.atomic():
        TipoSancion.objects.create(pk=78, nombre_sancion="Otro", duracion=168)
    with pytest.raises(IntegrityError), transaction.atomic():
        TipoSancion.objects.filter(pk=74).update(duracion=48)


def test_registro_no_cambia_rol_de_administrador(escenario_auditoria):
    _, admin, _, _ = escenario_auditoria
    admin.password_hash = ""
    admin.save(update_fields=["password_hash"])
    with pytest.raises(RegistrationError, match="solicitantes"):
        register_student_account(admin.pk, admin.email, "clave-segura")
    admin.refresh_from_db()
    assert admin.password_hash == ""
    assert admin.rol.nombre_rol == "Administrador"


def test_auditoria_rechaza_acciones_fuera_del_catalogo(escenario_auditoria):
    ana, _, bloques, _ = escenario_auditoria
    reserva = services.create_student_reservation(ana.pk, bloques[0].pk, "Tarea")
    with pytest.raises(IntegrityError), transaction.atomic():
        Auditoria.objects.create(reserva=reserva, actor=ana, accion="RESERVAR")
