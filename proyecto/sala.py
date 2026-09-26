class Room:
    """Una sala de estudio con identificador, nombre, capacidad."""
    def __init__(self, room_id, name, capacity):
        self.room_id = room_id
        self.name = name
        self.capacity = capacity

    def has_capacity(self, attendees):
        """¿Hay espacio para N asistentes?"""
        return attendees <= self.capacity