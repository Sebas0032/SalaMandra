"""Pruebas de las reglas de negocio.

Cada prueba debe:
- Tener un nombre que empiece con test_ y describa el comportamiento
  (ej. test_rechaza_codigo_con_formato_invalido).
- Preparar el estado/entradas, invocar la función real y comparar
  el resultado (y el estado posterior, si aplica) con lo acordado.
- Estar basada en uno de los ejemplos de docs/sesion04.md, no en un
  valor inventado sin regla que lo respalde.

from proyecto.reglas import ...  # importen aquí lo que vayan probando
"""
from proyecto import Room, Student, Reservation, create_reservation
from proyecto.excepciones import (
    RoomNotFoundError,
    CapacityExceededError,
    StudentAlreadyBookedError,
    TimeConflictError
)


class TestCrearReservaUsoCasoNormal:
    """CASO 1: Uso normal — reserva exitosa."""

    def test_crear_reserva_caso_normal(self):
        """
        Estado inicial: el solicitante con código 92345 está registrado.
        La Sala de estudio A (capacidad 6) está libre en el bloque de 10:00 a 12:00.

        Entrada: el estudiante ingresa código 92345, sala Sala de estudio A,
        horario 10:00 a 12:00 y 4 asistentes.

        Resultado esperado: El sistema valida los datos, registra la reserva
        y retorna un estado CONFIRMADA con un ID de reserva.
        """
        # Armar datos
        room = Room("A-101", "Sala de estudio A", 6)
        rooms = {"A-101": room}
        reservations = []

        # Llamar la función
        result = create_reservation(
            rooms=rooms,
            reservations=reservations,
            room_id="A-101",
            student_code="92345",
            start="10:00",
            end="12:00",
            attendees=4,
            activity_detail="Estudios"
        )

        # Verificar
        assert result.status == "CONFIRMADA"
        assert result.student_code == "92345"
        assert result.room_id == "A-101"
        assert result.start == "10:00"
        assert result.end == "12:00"
        assert result.activity_detail == "Estudios"
        assert len(reservations) == 1  # Se agregó a la lista


class TestCrearReservaLimite:
    """CASO 2: Límite — respeto del intervalo de 15 minutos entre reservas."""

    def test_crear_reserva_con_intervalo_de_desalojo(self):
        """
        Estado inicial: existe una reserva confirmada en la Sala de estudio A
        para el turno previo de 07:45 a 09:45.

        Entrada: el estudiante 92345 solicita reservar la misma Sala de estudio A
        para el turno inmediato siguiente de 10:00 a 12:00.

        Resultado esperado: Se procesa la solicitud exitosamente y retorna
        estado CONFIRMADA para el turno de 10:00 a 12:00.

        Regla: El término de un turno (09:45) y el inicio del siguiente (10:00)
        respetan la separación de 15 minutos entre bloques.
        """
        # Armar datos
        room = Room("A-101", "Sala de estudio A", 6)
        rooms = {"A-101": room}

        # Crear una reserva anterior (07:45 a 09:45)
        existing_reservation = Reservation(
            reservation_id=1,
            room_id="A-101",
            student_code="99999",
            start="07:45",
            end="09:45",
            activity_detail="Estudios",
            status="CONFIRMADA"
        )
        reservations = [existing_reservation]

        # Intenta crear una reserva en 10:00 a 12:00 (respeta el intervalo de 15 min)
        # Nota: esta prueba fallará hasta que implementes has_time_conflict
        result = create_reservation(
            rooms=rooms,
            reservations=reservations,
            room_id="A-101",
            student_code="92345",
            start="10:00",
            end="12:00",
            attendees=4,
            activity_detail="Tareas"
        )

        # Verificar
        assert result.status == "CONFIRMADA"
        assert len(reservations) == 2  # La nueva se agregó
        assert reservations[0].student_code == "99999"  # La anterior sigue igual
        assert reservations[1].student_code == "92345"

