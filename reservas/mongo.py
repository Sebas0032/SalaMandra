"""
Conexión a MongoDB usando pymongo directamente (sin el ORM de Django).

Colecciones que usa este proyecto, dentro de la base de datos
`settings.MONGO_DB_NAME`:

    rooms           Salas de estudio (room_id, name, capacity)
    reservations    Reservas (room_id, student_code, start, end, status, ...)
    bloqueos        Bloqueos de horario por mantenimiento (RES-RF-03)
    admins          Usuarios con rol Administrador (username, password_hash)

No hay "modelos" de Django: cada documento es simplemente un dict de
Python que entra y sale de MongoDB tal cual, a través de las funciones
de reservas/services.py.
"""

from django.conf import settings
from pymongo import MongoClient

_client = None


def get_client():
    """Devuelve un único MongoClient reutilizable para todo el proceso."""
    global _client
    if _client is None:
        _client = MongoClient(
            settings.MONGO_URI,
            serverSelectionTimeoutMS=5000,  # falla rápido si Mongo no responde
        )
    return _client


def get_db():
    """Devuelve la base de datos de SalaMandra (salamandra_db por defecto)."""
    return get_client()[settings.MONGO_DB_NAME]
