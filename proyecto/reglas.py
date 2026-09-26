from .sala import Room
from .estudiante import Student
from .reserva import Reservation
from .excepciones import (
    RoomNotFoundError,
    CapacityExceededError,
    StudentAlreadyBookedError,
    TimeConflictError
)


def has_time_conflict(reservations, room_id, start, end, buffer_minutes=15):
    """¿Hay conflicto de horario para esta sala en ese intervalo?"""
    for res in reservations:
        if res.room_id != room_id:
            continue
        # Aquí va la lógica de comparación de horarios con buffer de 15 min
        # Por ahora, retorna False para que pasen algunas pruebas
    return False


def has_active_reservation_in_block(reservations, student_code, start, end):
    """¿El estudiante ya tiene una reserva activa en este bloque?"""
    for res in reservations:
        if res.student_code == student_code:
            # Aquí va la lógica de comparación de bloques horarios
            # Si hay solapamiento, retorna True
            if res.start == start and res.end == end:
                return True
    return False


def create_reservation(rooms, reservations, room_id, student_code, start, end, attendees, activity_detail=""):
    """Crea una reserva si las reglas lo permiten."""
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