"""
Lógica de negocio del caso de uso RES-CU-02 (docs/sesion-07-modelos.md):
"Bloquear un horario de una sala por mantenimiento".

Esta función implementa, paso a paso, el flujo descrito en la Sesión 07:

    1. El Administrador selecciona la sala y el horario a bloquear.
    2. El sistema valida que la sala exista y que el usuario tenga
       permisos de Administrador.                              -> E1, E2
    3. El sistema verifica que el horario no esté ya en MANTENIMIENTO.
    4. El sistema busca si existe una reserva CONFIRMADA en ese horario.
    5. Si existe, la cambia a POR_MANTENIMIENTO (sin penalización).
    6. El sistema registra el bloqueo del horario (colección `bloqueos`).
    7. Se guarda el motivo y la fecha/hora del bloqueo.
    8. Se confirma el resultado (y se informa qué reserva se canceló,
       si había alguna).

No se usa el ORM de Django: todo el acceso a datos pasa por
`reservas/mongo.py` (pymongo) contra MongoDB.
"""

from datetime import datetime, timezone

from .mongo import get_db


class RoomNotFoundError(Exception):
    """La sala indicada no existe en el sistema (rama E2)."""


class NotAuthorizedError(Exception):
    """Quien solicita el bloqueo no tiene rol de Administrador (rama E1)."""


class ScheduleAlreadyBlockedError(Exception):
    """Ese horario de esa sala ya está en estado MANTENIMIENTO."""


# --- Lecturas simples, para mostrar el estado del sistema en el dashboard ---

def get_rooms():
    db = get_db()
    return list(db.rooms.find().sort("room_id", 1))


def get_room(room_id):
    db = get_db()
    return db.rooms.find_one({"room_id": room_id})


def get_reservations():
    db = get_db()
    return list(db.reservations.find().sort([("room_id", 1), ("start", 1)]))


def get_bloqueos():
    db = get_db()
    return list(db.bloqueos.find().sort("fecha_bloqueo", -1))


def _find_confirmed_reservation(room_id, start, end):
    db = get_db()
    return db.reservations.find_one(
        {
            "room_id": room_id,
            "start": start,
            "end": end,
            "status": "CONFIRMADA",
        }
    )


def _is_schedule_blocked(room_id, start, end):
    db = get_db()
    return (
        db.bloqueos.find_one({"room_id": room_id, "start": start, "end": end})
        is not None
    )


# --- Caso de uso RES-CU-02 --------------------------------------------------

def block_room_schedule_for_maintenance(is_admin, room_id, start, end, motivo):
    """
    Bloquea un horario (start-end) de una sala por mantenimiento.

    Parámetros:
        is_admin (bool): si quien solicita el bloqueo tiene rol Administrador.
        room_id (str):   identificador de la sala, ej. "A-101".
        start, end (str): horario en formato "HH:MM", ej. "15:00", "17:00".
        motivo (str):    razón del bloqueo, ej. "Fuga de agua".

    Devuelve un dict con el resultado. Lanza una excepción si el sistema
    debe rechazar la operación (ramas E1 / E2 / horario ya bloqueado).
    """
    # Paso 2 (parte 1) — E1: sin permisos de Administrador
    if not is_admin:
        raise NotAuthorizedError(
            "No tienes permisos para bloquear salas. Contacta al administrador."
        )

    # Paso 2 (parte 2) — E2: la sala no existe
    room = get_room(room_id)
    if room is None:
        raise RoomNotFoundError(f"La sala {room_id} no existe en el sistema.")

    # Paso 3 — el horario ya está en mantenimiento
    if _is_schedule_blocked(room_id, start, end):
        raise ScheduleAlreadyBlockedError(
            f"El horario {start}-{end} de la sala {room_id} ya está en "
            "mantenimiento."
        )

    db = get_db()

    # Paso 4 — buscar si hay una reserva confirmada en ese horario exacto
    reserva = _find_confirmed_reservation(room_id, start, end)
    reserva_cancelada = None

    # Paso 5 — si existe, pasa a POR_MANTENIMIENTO, sin penalización
    if reserva is not None:
        db.reservations.update_one(
            {"_id": reserva["_id"]},
            {"$set": {"status": "POR_MANTENIMIENTO"}},
        )
        reserva_cancelada = db.reservations.find_one({"_id": reserva["_id"]})

    # Paso 6 y 7 — registrar el bloqueo del horario, con motivo y fecha
    bloqueo = {
        "room_id": room_id,
        "room_name": room.get("name", room_id),
        "start": start,
        "end": end,
        "motivo": motivo,
        "fecha_bloqueo": datetime.now(timezone.utc),
    }
    db.bloqueos.insert_one(bloqueo)

    # Paso 8 — confirmar el resultado
    return {
        "room_id": room_id,
        "start": start,
        "end": end,
        "motivo": motivo,
        "reserva_cancelada": reserva_cancelada,
    }
