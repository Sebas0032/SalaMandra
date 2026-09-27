from .sala import Room
from .estudiante import Student
from .reserva import Reservation
from .excepciones import (
    RoomNotFoundError,
    CapacityExceededError,
    StudentAlreadyBookedError,
    TimeConflictError,
    StudentNotFoundError
)

def validate_student(students, student_code):
    """Verifica que el codigo del estudiante este registrado."""
    student = students.get(student_code)
    if student is None:
        raise StudentNotFoundError(
            f"El estudiante con codigo {student_code} no esta registrado"
        )
    return student


def has_time_conflict(reservations, room_id, start, end, buffer_minutes=15):
    """Verifica si existe conflicto de horario para una sala."""

    from datetime import datetime, timedelta

    new_start = datetime.strptime(start, "%H:%M")
    new_end = datetime.strptime(end, "%H:%M")

    for res in reservations:
        if res.room_id != room_id:
            continue

        existing_start = datetime.strptime(res.start, "%H:%M")
        existing_end = datetime.strptime(res.end, "%H:%M")

        existing_end_with_buffer = existing_end + timedelta(minutes=buffer_minutes)

        if new_start < existing_end_with_buffer and new_end > existing_start:
            return True

    return False


def has_active_reservation_in_block(reservations, student_code, start, end):
    """Verifica si el estudiante ya tiene una reserva activa en ese bloque."""

    from datetime import datetime

    new_start = datetime.strptime(start, "%H:%M")
    new_end = datetime.strptime(end, "%H:%M")

    for res in reservations:
        if res.student_code != student_code:
            continue

        existing_start = datetime.strptime(res.start, "%H:%M")
        existing_end = datetime.strptime(res.end, "%H:%M")

        if new_start < existing_end and new_end > existing_start:
            return True

    return False


def create_reservation(students, rooms, reservations, room_id, student_code, start, end, attendees, activity_detail=""):
    """Crea una reserva si las reglas lo permiten."""
    # Validar estudiante
    validate_student(students, student_code)

    # Buscar la sala
    room = rooms.get(room_id)
    if not room:
        raise RoomNotFoundError(f"Sala {room_id} no existe")

    # Validar capacidad
    if not room.has_capacity(attendees):
        raise CapacityExceededError(f"Capacidad de {room.capacity} insuficiente para {attendees}")

    # Validar conflicto de horario en la sala
    if has_time_conflict(reservations, room_id, start, end):
        raise TimeConflictError(f"La sala {room_id} ya está reservada en ese horario")

    # Validar que el estudiante no tenga otra reserva en ese bloque
    if has_active_reservation_in_block(reservations, student_code, start, end):
        raise StudentAlreadyBookedError(f"El estudiante {student_code} ya tiene una reserva en ese bloque")

    # Si todo está bien, crear la reserva
    reservation = Reservation(
        reservation_id=len(reservations) + 1,
        room_id=room_id,
        student_code=student_code,
        start=start,
        end=end,
        activity_detail=activity_detail,
        status="CONFIRMADA"
    )
    reservations.append(reservation)
    return reservation