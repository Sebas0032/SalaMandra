"""
Lógica de negocio del caso de uso RES-CU-02 (docs/sesion-07-modelos.md):
"Bloquear un horario de una sala por mantenimiento".

Flujo de `block_room_schedule_for_maintenance`, paso a paso:

    1. El Administrador selecciona la sala y el horario (= una fila de
       `sala_horario`) que quiere bloquear.
    2. El sistema valida que quien lo pide tenga rol Administrador   -> E1
       y que esa combinación sala+horario exista.                    -> E2
    3. El sistema verifica que no esté ya en MANTENIMIENTO.
    4. Busca las reservas CONFIRMADA asociadas a ese sala_horario.
    5. Las cambia a POR_MANTENIMIENTO (sin penalización).
    6. Cambia sala_horario.estado_sala_horario a MANTENIMIENTO.
    7. Registra el bloqueo (quién, motivo, fecha) en `bloqueos`.
    8. Devuelve el resultado, indicando qué reservas se cancelaron.

Todo ocurre dentro de UNA transacción: o se hacen todos los cambios, o no
se hace ninguno (por ejemplo, si algo falla en el paso 7, la sala no queda
en MANTENIMIENTO con reservas a medio cancelar).
"""

from django.contrib.auth.hashers import check_password
from django.db import transaction

from .models import Bloqueo, Reserva, SalaHorario, Usuario, UsuarioRol

ROL_ADMINISTRADOR = "Administrador"


class ScheduleNotFoundError(Exception):
    """No existe esa combinación de sala y horario (rama E2)."""


class NotAuthorizedError(Exception):
    """Quien solicita el bloqueo no tiene rol de Administrador (rama E1)."""


class ScheduleAlreadyBlockedError(Exception):
    """Ese sala_horario ya está en estado MANTENIMIENTO."""


# --- Autenticación -----------------------------------------------------

def usuario_tiene_rol(codigo_usuario, nombre_rol):
    return UsuarioRol.objects.filter(
        usuario_id=codigo_usuario, rol__nombre_rol=nombre_rol
    ).exists()


def authenticate_admin(email, password):
    """Devuelve el Usuario si el correo/contraseña son correctos, la cuenta
    está activa (estado_usuario) y tiene el rol Administrador. Si no, None."""
    usuario = Usuario.objects.filter(email=email).first()
    if usuario is None or not usuario.estado_usuario:
        return None
    if not usuario.password_hash or not check_password(
        password, usuario.password_hash
    ):
        return None
    if not usuario_tiene_rol(usuario.codigo_usuario, ROL_ADMINISTRADOR):
        return None
    return usuario


# --- Lecturas para mostrar el estado del sistema ----------------------------

def get_sala_horarios():
    return SalaHorario.objects.select_related("sala", "horario").order_by(
        "id_sala_horario"
    )


def get_reservas():
    return Reserva.objects.select_related(
        "usuario", "sala_horario__sala", "sala_horario__horario"
    ).order_by("id_reserva")


def get_bloqueos():
    return Bloqueo.objects.select_related(
        "usuario", "sala_horario__sala", "sala_horario__horario"
    ).order_by("-fecha")


# --- Caso de uso RES-CU-02 --------------------------------------------------

@transaction.atomic
def block_room_schedule_for_maintenance(codigo_usuario_admin, id_sala_horario, motivo):
    """
    Bloquea por mantenimiento una combinación sala+horario.

    Lanza NotAuthorizedError (E1), ScheduleNotFoundError (E2) o
    ScheduleAlreadyBlockedError si el sistema debe rechazar la operación.
    """
    # Paso 2 (parte 1) — E1: sin permisos de Administrador
    if not usuario_tiene_rol(codigo_usuario_admin, ROL_ADMINISTRADOR):
        raise NotAuthorizedError(
            "No tienes permisos para bloquear salas. Contacta al administrador."
        )

    # Paso 2 (parte 2) — E2: la combinación sala+horario no existe
    try:
        sala_horario = SalaHorario.objects.select_related("sala", "horario").get(
            pk=id_sala_horario
        )
    except SalaHorario.DoesNotExist:
        raise ScheduleNotFoundError(
            f"No existe una combinación de sala y horario con id {id_sala_horario}."
        )

    # Paso 3 — ya está en mantenimiento
    if sala_horario.estado_sala_horario == SalaHorario.ESTADO_MANTENIMIENTO:
        raise ScheduleAlreadyBlockedError(
            f"El horario {sala_horario.horario} de la sala "
            f"{sala_horario.sala} ya está en mantenimiento."
        )

    # Paso 4 y 5 — reservas CONFIRMADA -> POR_MANTENIMIENTO (sin penalización)
    reservas_canceladas = list(
        Reserva.objects.select_related("usuario").filter(
            sala_horario=sala_horario,
            estado_reserva=Reserva.ESTADO_CONFIRMADA,
        )
    )
    Reserva.objects.filter(pk__in=[r.pk for r in reservas_canceladas]).update(
        estado_reserva=Reserva.ESTADO_POR_MANTENIMIENTO
    )

    # Paso 6 — el horario de la sala pasa a MANTENIMIENTO
    sala_horario.estado_sala_horario = SalaHorario.ESTADO_MANTENIMIENTO
    sala_horario.save(update_fields=["estado_sala_horario"])

    # Paso 7 — registrar el bloqueo (quién, motivo, cuándo)
    Bloqueo.objects.create(
        usuario_id=codigo_usuario_admin,
        sala_horario=sala_horario,
        motivo=motivo,
    )

    # Paso 8 — confirmar el resultado
    return {
        "sala_horario": sala_horario,
        "reservas_canceladas": reservas_canceladas,
    }
