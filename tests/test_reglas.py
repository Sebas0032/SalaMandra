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
from proyecto import Room, Student, Reservation, create_reservation, validate_student
from proyecto.excepciones import (
    RoomNotFoundError,
    CapacityExceededError,
    StudentAlreadyBookedError,
    TimeConflictError,
    StudentNotFoundError
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

        students = {
            "92345": Student("92345", "Luciana", "Perez")
        }

        # Armar datos
        room = Room("A-101", "Sala de estudio A", 6)
        rooms = {"A-101": room}
        reservations = []


        # Llamar la función
        result = create_reservation(
            students=students,
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


class TestValidacionEstudiante:

    def test_acepta_codigo_de_estudiante_registrado(self):
        students = {
            "92345": Student("92345", "Luciana", "Perez")
        }

        student = validate_student(students, "92345")

        assert student.code == "92345"
        assert student.first_name == "Luciana"
        assert student.last_name == "Perez"
        assert student.full_name() == "Luciana Perez"

    def test_rechaza_codigo_de_estudiante_no_registrado(self):
        students = {
            "92345": Student("92345", "Luciana", "Perez")
        }

        from pytest import raises

        with raises(StudentNotFoundError):
            validate_student(students, "99999")


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

        students = {
            "92345": Student("92345", "Luciana", "Perez"),
            "99999": Student("99999", "Carlos", "Gomez")
        }

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
            students=students,
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


class TestCrearReservaRechazo:
    """CASO 3: Rechazo — un alumno no puede reservar dos salas en el mismo bloque."""

    def test_rechaza_si_estudiante_ya_tiene_reserva_en_bloque(self):
        """
        Estado inicial: el estudiante con código 92345 ya tiene una reserva activa
        en otra sala (ej. Sala B) para el bloque de 10:00 a 12:00.

        Entrada: intenta realizar una segunda reserva para la Sala de estudio A
        en el mismo bloque de 10:00 a 12:00.

        Resultado esperado: El sistema rechaza la nueva reserva, conserva
        la reserva existente e informa que el alumno ya cuenta con un espacio
        reservado en ese horario.
        """
        # Armar datos
        room_a = Room("A-101", "Sala de estudio A", 6)
        room_b = Room("B-102", "Sala de estudio B", 4)
        rooms = {"A-101": room_a, "B-102": room_b}

        students = {
            "92345": Student("92345", "Luciana", "Perez"),
            "99999": Student("99999", "Carlos", "Gomez")
        }

        # El estudiante 92345 ya tiene una reserva en Sala B para 10:00-12:00
        existing_reservation = Reservation(
            reservation_id=1,
            room_id="B-102",
            student_code="92345",
            start="10:00",
            end="12:00",
            activity_detail="Haciendo tareas",
            status="CONFIRMADA"
        )
        reservations = [existing_reservation]

        # Intenta crear otra reserva en Sala A para el mismo horario
        # Debe lanzar StudentAlreadyBookedError
        from pytest import raises

        with raises(StudentAlreadyBookedError) as exc_info:
            create_reservation(
                students=students,
                rooms=rooms,
                reservations=reservations,
                room_id="A-101",
                student_code="92345",
                start="10:00",
                end="12:00",
                attendees=3,
                activity_detail="Estudios"
            )

        # Verificar que el error contiene el código del estudiante
        assert "92345" in str(exc_info.value)
        # Verificar que la lista no cambió (no se agregó la reserva)
        assert len(reservations) == 1

    def test_rechaza_reserva_si_codigo_no_esta_registrado(self):
        students = {
            "92345": Student("92345", "Luciana", "Perez")
        }

        room = Room("A-101", "Sala de estudio A", 6)
        rooms = {"A-101": room}
        reservations = []

        from pytest import raises

        with raises(StudentNotFoundError):
            create_reservation(
                students=students,
                rooms=rooms,
                reservations=reservations,
                room_id="A-101",
                student_code="99999",
                start="10:00",
                end="12:00",
                attendees=4,
                activity_detail="Estudios"
            )

        assert len(reservations) == 0

# Pruebas adicionales para validaciones básicas

class TestValidacionesSala:
    """Pruebas para validaciones de sala."""

    def test_rechaza_si_sala_no_existe(self):
        """Rechaza reserva si la sala no existe en el inventario."""
        rooms = {}  # Inventario vacío
        reservations = []

        students = {
            "92345": Student("92345", "Luciana", "Perez")
        }

        from pytest import raises

        with raises(RoomNotFoundError) as exc_info:
            create_reservation(
                students=students,
                rooms=rooms,
                reservations=reservations,
                room_id="Z-999",
                student_code="92345",
                start="10:00",
                end="12:00",
                attendees=2,
                activity_detail="Estudios"
            )

        assert "Z-999" in str(exc_info.value)

    def test_rechaza_si_asistentes_exceden_capacidad(self):
        """Rechaza reserva si el número de asistentes supera la capacidad."""
        room = Room("A-101", "Sala de estudio A", 3)  # Capacidad 3
        rooms = {"A-101": room}
        reservations = []

        students = {
            "92345": Student("92345", "Luciana", "Perez")
        }

        from pytest import raises

        with raises(CapacityExceededError):
            create_reservation(
                students=students,
                rooms=rooms,
                reservations=reservations,
                room_id="A-101",
                student_code="92345",
                start="10:00",
                end="12:00",
                attendees=5,  # Intenta 5 en sala de 3
                activity_detail="Estudios"
            )

