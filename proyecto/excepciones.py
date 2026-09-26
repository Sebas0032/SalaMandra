"""Excepciones personalizadas del proyecto."""
class RoomNotFoundError(Exception):
    """La sala solicitada no existe en el inventario."""
    pass


class CapacityExceededError(Exception):
    """El número de asistentes supera la capacidad de la sala."""
    pass


class StudentAlreadyBookedError(Exception):
    """El estudiante ya tiene una reserva en ese bloque horario."""
    pass


class TimeConflictError(Exception):
    """La sala ya tiene una reserva en ese intervalo de tiempo."""
    pass

